"""
ai_inference.py

Module d'inférence IA pour le dashboard Robocar.
- Segmentation de route (OpenVINO road-segmentation)
- Détection d'objets (YOLOv8)
- Détection de places de parking
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict
import threading
import time

try:
    from openvino.runtime import Core
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    logging.warning("OpenVINO non disponible. Installez: pip install openvino")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLOv8 non disponible. Installez: pip install ultralytics")


class AIInference:
    """
    Gestionnaire d'inférence IA pour le dashboard.
    Thread-safe, traite les frames vidéo en temps réel.
    """
    
    def __init__(self, enable_segmentation: bool = True, enable_detection: bool = True):
        """
        Initialise les modèles IA.
        
        Args:
            enable_segmentation: Activer la segmentation de route
            enable_detection: Activer la détection d'objets YOLOv8
        """
        self.logger = logging.getLogger('AIInference')
        
        self.enable_segmentation = enable_segmentation and OPENVINO_AVAILABLE
        self.enable_detection = enable_detection and YOLO_AVAILABLE
        
        # Modèles
        self.road_seg_model = None
        self.yolo_model = None
        
        # Thread-safe
        self.processing_lock = threading.Lock()
        
        # Stats
        self.inference_time = 0.0
        self.fps = 0.0
        
        # Mode d'affichage
        self.mask_mode = False
        
        # Marquages détectés (pour affichage)
        self.detected_markings = []
        
        # Charger modèles
        if self.enable_segmentation:
            self._load_road_segmentation()
        
        if self.enable_detection:
            self._load_yolo()
        
        self.logger.info(f"AIInference initialisé (seg={self.enable_segmentation}, det={self.enable_detection})")
    
    def _load_road_segmentation(self):
        """Charge le modèle OpenVINO road-segmentation"""
        try:
            self.logger.info("Chargement road-segmentation OpenVINO...")
            ie = Core()
            
            # Télécharger le modèle depuis Open Model Zoo
            # road-segmentation-adas-0001
            model_path = "models/intel/road-segmentation-adas-0001/FP32/road-segmentation-adas-0001.xml"
            
            try:
                self.road_seg_model = ie.read_model(model=model_path)
                self.road_seg_compiled = ie.compile_model(self.road_seg_model, "CPU")
                self.road_seg_input_layer = self.road_seg_compiled.input(0)
                self.road_seg_output_layer = self.road_seg_compiled.output(0)
                
                self.logger.info(f"✅ Road segmentation chargé: {model_path}")
            except:
                self.logger.warning("Modèle road-segmentation non trouvé. Utilisation de fallback HSV...")
                self.enable_segmentation = False  # Utiliser fallback au lieu du modèle
                
        except Exception as e:
            self.logger.error(f"Erreur chargement road-segmentation: {e}")
            self.enable_segmentation = False
    
    def _load_yolo(self):
        """Charge le modèle YOLOv8"""
        try:
            self.logger.info("Chargement YOLOv8...")
            
            # Charger YOLOv8n (nano, le plus rapide)
            self.yolo_model = YOLO('yolov8n.pt')
            
            # Classes d'intérêt pour la route
            self.target_classes = [
                0,   # person
                1,   # bicycle
                2,   # car
                3,   # motorcycle
                5,   # bus
                7,   # truck
                9,   # traffic light
                11,  # stop sign
            ]
            
            self.logger.info("✅ YOLOv8 chargé")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement YOLOv8: {e}")
            self.enable_detection = False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Traite une frame avec les modèles IA.
        
        Args:
            frame: Frame vidéo RGB
            
        Returns:
            (frame_with_overlay, info_dict)
        """
        if frame is None or frame.size == 0:
            return frame, {}
        
        start_time = time.time()
        
        with self.processing_lock:
            overlay = frame.copy()
            info = {
                'road_detected': False,
                'objects': [],
                'parking_spots': [],
                'inference_time_ms': 0
            }
            
            # Segmentation de route
            road_mask = None
            if self.enable_segmentation:
                road_mask = self._segment_road(frame)
                if road_mask is not None:
                    info['road_detected'] = True
            
            # Détection d'objets
            detections = []
            if self.enable_detection:
                detections = self._detect_objects(frame)
                info['objects'] = detections
            
            # Détection de places de parking (améliorée)
            parking_spots = self._detect_parking_spots_improved(frame, detections)
            info['parking_spots'] = parking_spots
            
            # Mode masque: afficher seulement les zones détectées
            if self.mask_mode:
                overlay = self._render_mask_mode(frame, road_mask, detections, parking_spots)
            else:
                # Mode normal: overlay sur vidéo
                if road_mask is not None:
                    overlay = self._overlay_segmentation(overlay, road_mask)
                overlay = self._draw_detections(overlay, detections)
                overlay = self._draw_parking_spots(overlay, parking_spots)
            
            # Stats
            self.inference_time = (time.time() - start_time) * 1000
            info['inference_time_ms'] = self.inference_time
            self.fps = 1000.0 / self.inference_time if self.inference_time > 0 else 0
            
            return overlay, info
    
    def _segment_road(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Segmente la route avec OpenVINO ou fallback HSV"""
        if not self.enable_segmentation:
            return None
        
        # Essayer avec le modèle OpenVINO d'abord
        if self.road_seg_model is not None:
            try:
                # Préparer l'input (512x896 pour road-segmentation-adas-0001)
                input_h, input_w = 512, 896
                resized = cv2.resize(frame, (input_w, input_h))
                input_tensor = np.expand_dims(resized.transpose(2, 0, 1), 0).astype(np.float32)
                
                # Inférence
                result = self.road_seg_compiled([input_tensor])[self.road_seg_output_layer]
                
                # Post-traitement: classe 1 = route
                mask = np.argmax(result[0], axis=0).astype(np.uint8)
                road_mask = (mask == 1).astype(np.uint8) * 255
                
                # Resize au format original
                road_mask = cv2.resize(road_mask, (frame.shape[1], frame.shape[0]))
                
                return road_mask
                
            except Exception as e:
                self.logger.error(f"Erreur segmentation OpenVINO: {e}")
                return self._segment_road_hsv_fallback(frame)
        else:
            # Fallback: segmentation basée sur HSV
            return self._segment_road_hsv_fallback(frame)
    
    def _segment_road_hsv_fallback(self, frame: np.ndarray) -> np.ndarray:
        """
        Fallback: segmentation de route basée sur HSV.
        Détecte les routes grises/noires (route typique).
        """
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Route: teinte variable, saturation basse, valeur moyenne-basse
            # Routes grises: S<50, V: 80-180
            # Routes noires/sombres: V<100
            lower_dark = np.array([0, 0, 30])      # Très sombre
            upper_dark = np.array([180, 50, 100])  # Gris foncé
            
            # Routes grises clair
            lower_gray = np.array([0, 0, 100])
            upper_gray = np.array([180, 40, 200])
            
            # Combiner les masques
            mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)
            mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
            road_mask = cv2.bitwise_or(mask_dark, mask_gray)
            
            # Morphologie pour nettoyer
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return road_mask
            
        except Exception as e:
            self.logger.error(f"Erreur segmentation fallback HSV: {e}")
            return None
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Détecte les objets avec YOLOv8"""
        if not self.enable_detection or self.yolo_model is None:
            return []
        
        try:
            # Inférence YOLOv8 (mode fast)
            results = self.yolo_model(frame, verbose=False, conf=0.4)[0]
            
            detections = []
            for box in results.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Filtrer les classes d'intérêt
                if cls in self.target_classes:
                    detections.append({
                        'class': cls,
                        'class_name': results.names[cls],
                        'confidence': conf,
                        'bbox': (int(x1), int(y1), int(x2), int(y2))
                    })
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Erreur détection: {e}")
            return []
    
    def _detect_parking_spots_improved(self, frame: np.ndarray, objects: List[Dict]) -> List[Dict]:
        """
        Détection améliorée de places de parking.
        Analyse la partie basse de l'image (zone au sol devant le véhicule).
        """
        parking_spots = []
        
        try:
            h, w = frame.shape[:2]
            
            # Zone d'intérêt: partie basse de l'image (50% à 100% hauteur)
            roi_y_start = int(h * 0.5)
            roi = frame[roi_y_start:, :]
            
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Détecter les marquages blancs (bandes)
            white_mask = cv2.inRange(gray, 200, 255)
            
            # Détecter les bords (marquages au sol)
            edges = cv2.Canny(gray, 50, 150)
            
            # Combiner marquages blancs et edges
            combined = cv2.bitwise_or(white_mask, edges)
            
            # Détecter les lignes (marquages de parking)
            lines = cv2.HoughLinesP(combined, 1, np.pi/180, 40, minLineLength=25, maxLineGap=15)
            
            # Zones où il y a des véhicules
            vehicle_zones = []
            for obj in objects:
                if obj['class'] in [2, 3, 5, 7]:  # car, motorcycle, bus, truck
                    x1, y1, x2, y2 = obj['bbox']
                    # Ajuster pour la ROI
                    if y2 > roi_y_start:
                        vehicle_zones.append((x1, max(0, y1 - roi_y_start), x2, y2 - roi_y_start))
            
            # Stocker les marquages détectés pour l'affichage avec leur offset Y
            self.detected_markings = lines if lines is not None else []
            self.detected_markings_offset = roi_y_start
            
            if lines is not None and len(lines) >= 2:
                # Regrouper les lignes verticales/quasi-verticales proches
                vertical_lines = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    # Lignes quasi-verticales (50-130 degrés)
                    if 50 < angle < 130:
                        x_center = (x1 + x2) // 2
                        vertical_lines.append(x_center)
                
                # Trier et regrouper les lignes proches
                if len(vertical_lines) >= 2:
                    vertical_lines = sorted(vertical_lines)
                    
                    # Fusionner les lignes proches (même délimitation)
                    merged_lines = []
                    i = 0
                    while i < len(vertical_lines):
                        cluster = [vertical_lines[i]]
                        while i + 1 < len(vertical_lines) and vertical_lines[i + 1] - vertical_lines[i] < 20:
                            i += 1
                            cluster.append(vertical_lines[i])
                        merged_lines.append(int(np.mean(cluster)))
                        i += 1
                    
                    # Détecter des paires de lignes (délimitant une place)
                    for i in range(len(merged_lines) - 1):
                        x1 = merged_lines[i]
                        x2 = merged_lines[i + 1]
                        
                        # Largeur de place typique: 2m-3m = 70-200 pixels
                        width = x2 - x1
                        if 70 < width < 220:
                            # Vérifier qu'il n'y a pas de véhicule
                            occupied = False
                            y1 = 0
                            y2 = roi.shape[0]
                            
                            for vx1, vy1, vx2, vy2 in vehicle_zones:
                                # Intersection
                                if not (x2 < vx1 or x1 > vx2 or y2 < vy1 or y1 > vy2):
                                    occupied = True
                                    break
                            
                            if not occupied:
                                # Ajuster les coordonnées pour l'image complète
                                parking_spots.append({
                                    'bbox': (x1, roi_y_start + y1, x2, roi_y_start + y2),
                                    'area': width * (y2 - y1),
                                    'available': True,
                                    'confidence': 0.8
                                })
            
            # Méthode alternative: détecter zones vides rectangulaires sur zones grises
            if len(parking_spots) < 2:
                # Appliquer un seuillage pour détecter les zones sombres (absence de véhicule)
                thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY_INV, 15, 5)
                
                # Morphologie
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 10))
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
                
                # Trouver des rectangles de taille parking
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 2000 < area < 25000:
                        x, y, w_rect, h_rect = cv2.boundingRect(contour)
                        
                        # Aspect ratio parking (longer que haut, ou carré)
                        aspect = w_rect / h_rect if h_rect > 0 else 0
                        if 0.4 < aspect < 3.0:
                            occupied = False
                            for vx1, vy1, vx2, vy2 in vehicle_zones:
                                if not (x + w_rect < vx1 or x > vx2 or y + h_rect < vy1 or y > vy2):
                                    occupied = True
                                    break
                            
                            if not occupied and len(parking_spots) < 10:
                                parking_spots.append({
                                    'bbox': (x, roi_y_start + y, x + w_rect, roi_y_start + y + h_rect),
                                    'area': area,
                                    'available': True,
                                    'confidence': 0.6
                                })
            
            # Trier par confiance et limiter
            parking_spots = sorted(parking_spots, key=lambda x: x.get('confidence', 0), reverse=True)[:10]
            return parking_spots
            
        except Exception as e:
            self.logger.error(f"Erreur détection parking: {e}")
            return []
    
    def _overlay_segmentation(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Overlay la segmentation de route en bleu transparent"""
        overlay = frame.copy()
        
        # Colorier la route en bleu
        overlay[mask > 0] = overlay[mask > 0] * 0.6 + np.array([100, 100, 255]) * 0.4
        
        return overlay.astype(np.uint8)
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Dessine les détections YOLOv8"""
        overlay = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            conf = det['confidence']
            
            # Couleur selon la classe
            if det['class'] in [2, 3, 5, 7]:  # véhicules
                color = (0, 165, 255)  # Orange
            elif det['class'] == 0:  # personne
                color = (0, 0, 255)  # Rouge
            else:
                color = (255, 255, 0)  # Cyan
            
            # Rectangle
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{class_name} {conf:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(overlay, (x1, y1 - h - 5), (x1 + w, y1), color, -1)
            cv2.putText(overlay, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return overlay
    
    def _draw_parking_spots(self, frame: np.ndarray, spots: List[Dict]) -> np.ndarray:
        """Dessine les places de parking en vert"""
        overlay = frame.copy()
        
        for spot in spots:
            x1, y1, x2, y2 = spot['bbox']
            
            # Rectangle vert semi-transparent
            sub_img = overlay[y1:y2, x1:x2]
            green_rect = np.ones(sub_img.shape, dtype=np.uint8) * np.array([0, 255, 0])
            overlay[y1:y2, x1:x2] = cv2.addWeighted(sub_img, 0.6, green_rect, 0.4, 0)
            
            # Bordure
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Label "P"
            cv2.putText(overlay, "P", (x1 + 10, y1 + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        return overlay
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques d'inférence"""
        return {
            'inference_time_ms': self.inference_time,
            'fps': self.fps,
            'segmentation_enabled': self.enable_segmentation,
            'detection_enabled': self.enable_detection,
            'mask_mode': self.mask_mode
        }
    
    def toggle_mask_mode(self):
        """Bascule le mode masque"""
        self.mask_mode = not self.mask_mode
        return self.mask_mode
    
    def _render_mask_mode(self, frame: np.ndarray, road_mask: Optional[np.ndarray],
                         detections: List[Dict], parking_spots: List[Dict]) -> np.ndarray:
        """
        Mode masque: affiche uniquement les zones détectées sur fond noir.
        """
        h, w = frame.shape[:2]
        mask_view = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Route en bleu
        if road_mask is not None:
            mask_view[road_mask > 0] = [255, 150, 0]  # Bleu/cyan
        
        # Marquages blancs en JAUNE
        if self.detected_markings is not None and len(self.detected_markings) > 0:
            y_offset = getattr(self, 'detected_markings_offset', 0)
            for line in self.detected_markings:
                x1, y1, x2, y2 = line[0]
                # Ajuster les coordonnées Y avec l'offset du ROI
                cv2.line(mask_view, (x1, y1 + y_offset), (x2, y2 + y_offset), (0, 255, 255), 3)  # Jaune vif
        
        # Objets détectés
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            
            if det['class'] in [2, 3, 5, 7]:  # véhicules
                color = (0, 100, 255)  # Orange vif
            elif det['class'] == 0:  # personne
                color = (0, 0, 255)  # Rouge
            else:
                color = (255, 255, 0)  # Cyan
            
            # Zone remplie
            cv2.rectangle(mask_view, (x1, y1), (x2, y2), color, -1)
            # Bordure blanche
            cv2.rectangle(mask_view, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # Label
            label = f"{det['class_name']}"
            cv2.putText(mask_view, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Places de parking en vert brillant
        for spot in parking_spots:
            x1, y1, x2, y2 = spot['bbox']
            cv2.rectangle(mask_view, (x1, y1), (x2, y2), (0, 255, 0), -1)
            cv2.rectangle(mask_view, (x1, y1), (x2, y2), (255, 255, 255), 3)
            
            # "P" géant
            cv2.putText(mask_view, "P", (x1 + 20, y1 + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
        
        # Texte mode masque
        cv2.putText(mask_view, "MODE MASQUE (M pour quitter)", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Légende des couleurs
        legend_y = h - 80
        cv2.putText(mask_view, "LEGENDE:", (10, legend_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        cv2.rectangle(mask_view, (15, legend_y + 20), (35, legend_y + 35), (255, 150, 0), -1)
        cv2.putText(mask_view, "Route", (45, legend_y + 32),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.line(mask_view, (15, legend_y + 50), (35, legend_y + 50), (0, 255, 255), 3)
        cv2.putText(mask_view, "Marquages", (45, legend_y + 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.rectangle(mask_view, (200, legend_y + 20), (220, legend_y + 35), (0, 255, 0), -1)
        cv2.putText(mask_view, "Parking", (230, legend_y + 32),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.rectangle(mask_view, (320, legend_y + 20), (340, legend_y + 35), (0, 100, 255), -1)
        cv2.putText(mask_view, "Vehicules", (350, legend_y + 32),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return mask_view
