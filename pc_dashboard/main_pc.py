"""
main_pc.py

Dashboard de pilotage pour Robocar (Station Sol PC).

Fonctionnalités:
- Réception flux vidéo caméra (TCP 4488)
- Réception données lidar (UDP 15975)
- Envoi commandes de pilotage (UDP 5000)
- Interface graphique temps réel (OpenCV)
- Contrôle clavier
"""

import cv2
import numpy as np
import logging
import time
import argparse
import sys
from typing import Optional, List, Tuple

# Import des modules
from video_receiver import VideoReceiver
from lidar_receiver import LidarReceiver
from controller_sender import ControllerSender
from ai_inference import AIInference


class RobocarDashboard:
    """
    Dashboard principal de pilotage du Robocar.
    Gère l'affichage vidéo, lidar et le contrôle clavier.
    """
    
    def __init__(self, robot_ip: str, enable_ai: bool = True):
        """
        Initialise le dashboard.
        
        Args:
            robot_ip: Adresse IP du robot (ex: "10.84.106.222")
            enable_ai: Activer les fonctionnalités IA (segmentation, détection, parking)
        """
        self.robot_ip = robot_ip
        
        # Modules de communication (threads)
        self.video_receiver = VideoReceiver(robot_ip, port=4488)
        self.lidar_receiver = LidarReceiver(jetson_ip=robot_ip, port=15975)
        self.controller_sender = ControllerSender(robot_ip, port=5000)
        
        # Module IA
        self.enable_ai = enable_ai
        self.ai_inference = None
        if enable_ai:
            try:
                self.ai_inference = AIInference(
                    enable_segmentation=True,
                    enable_detection=True
                )
            except Exception as e:
                logging.error(f"Erreur initialisation IA: {e}")
                self.enable_ai = False
        
        # État de l'interface
        self.running = False
        
        # Fenêtres OpenCV
        self.window_video = "Robocar - Video Feed"
        self.window_lidar = "Robocar - Lidar View"
        
        # Dimensions
        self.video_width = 640
        self.video_height = 480
        self.lidar_size = 600  # Fenêtre carrée pour lidar
        
        # État du contrôle clavier
        self.throttle = 0.0
        self.steering = 0.0
        self.throttle_increment = 0.05
        self.steering_increment = 0.1
        
        # Logging
        self._setup_logging()
        
        # FPS tracking
        self.last_fps_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0
        
        self.logger.info("Dashboard initialisé")
    
    def _setup_logging(self):
        """Configure le système de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger('Dashboard')
    
    def start(self) -> bool:
        """
        Démarre tous les modules.
        
        Returns:
            True si démarrage réussi
        """
        self.logger.info("=== Démarrage du Dashboard ===")
        self.logger.info(f"Robot IP: {self.robot_ip}")
        
        # Démarrer modules de communication
        if not self.video_receiver.start():
            self.logger.error("Erreur démarrage VideoReceiver")
            return False
        
        if not self.lidar_receiver.start():
            self.logger.error("Erreur démarrage LidarReceiver")
            return False
        
        if not self.controller_sender.start():
            self.logger.error("Erreur démarrage ControllerSender")
            return False
        
        # Créer fenêtres
        cv2.namedWindow(self.window_video, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_video, self.video_width, self.video_height)
        
        cv2.namedWindow(self.window_lidar, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_lidar, self.lidar_size, self.lidar_size)
        
        self.running = True
        self.logger.info("✅ Dashboard démarré")
        
        return True
    
    def stop(self):
        """Arrête tous les modules."""
        self.logger.info("Arrêt du Dashboard...")
        self.running = False
        
        # Arrêter modules
        self.controller_sender.stop()
        self.video_receiver.stop()
        self.lidar_receiver.stop()
        
        # Fermer fenêtres
        cv2.destroyAllWindows()
        
        self.logger.info("Dashboard arrêté")
    
    def _process_keyboard(self, key: int):
        """
        Traite les touches clavier pour le contrôle.
        
        Args:
            key: Code de la touche (cv2.waitKey)
        """
        # Touches de contrôle
        if key == ord('z') or key == ord('Z'):
            # Accélérer
            self.throttle = min(1.0, self.throttle + self.throttle_increment)
            self.logger.debug(f"Throttle: {self.throttle:.2f}")
        
        elif key == ord('s') or key == ord('S'):
            # Freiner/Reculer
            self.throttle = max(-1.0, self.throttle - self.throttle_increment)
            self.logger.debug(f"Throttle: {self.throttle:.2f}")
        
        elif key == ord('q') or key == ord('Q'):
            # Tourner gauche
            self.steering = max(-1.0, self.steering - self.steering_increment)
            self.logger.debug(f"Steering: {self.steering:.2f}")
        
        elif key == ord('d') or key == ord('D'):
            # Tourner droite
            self.steering = min(1.0, self.steering + self.steering_increment)
            self.logger.debug(f"Steering: {self.steering:.2f}")
        
        elif key == ord(' '):
            # Frein d'urgence (espace)
            self.throttle = 0.0
            self.steering = 0.0
            self.controller_sender.send_command("emergency_stop")
            self.logger.warning("⚠️ ARRÊT D'URGENCE")
        
        elif key == ord('x') or key == ord('X'):
            # Recentrer (neutre)
            self.throttle = 0.0
            self.steering = 0.0
            self.logger.info("Position neutre")
        
        # Commandes ponctuelles
        elif key == ord('k') or key == ord('K'):
            # Klaxon
            self.controller_sender.send_command("horn")
            self.logger.info("🔊 Klaxon")
        
        elif key == ord('1'):
            self.controller_sender.send_command("sound_epitech")
            self.logger.info("🔊 Sound: Epitech")
        
        elif key == ord('2'):
            self.controller_sender.send_command("sound_satelisation")
            self.logger.info("🔊 Sound: Satelisation")
        
        elif key == ord('3'):
            self.controller_sender.send_command("sound_peter")
            self.logger.info("🔊 Sound: Peter")
        
        elif key == ord('4'):
            self.controller_sender.send_command("sound_polizia")
            self.logger.info("🔊 Sound: Polizia")
        
        elif key == ord('+') or key == ord('='):
            # Augmenter vitesse max
            self.controller_sender.send_command("increase_speed")
            self.logger.info("⬆️ Vitesse max +")
        
        elif key == ord('-') or key == ord('_'):
            # Diminuer vitesse max
            self.controller_sender.send_command("decrease_speed")
            self.logger.info("⬇️ Vitesse max -")
        
        elif key == ord('m') or key == ord('M'):
            # Toggle mode masque IA
            if self.enable_ai and self.ai_inference is not None:
                mask_mode = self.ai_inference.toggle_mask_mode()
                self.logger.info(f"🎭 Mode masque: {'ACTIVÉ' if mask_mode else 'DÉSACTIVÉ'}")
        
        # Mettre à jour le contrôle
        self.controller_sender.set_control(self.throttle, self.steering)
    
    def _render_video_frame(self, frame: Optional[np.ndarray]) -> np.ndarray:
        """
        Prépare la frame vidéo pour affichage avec overlay d'informations.
        
        Args:
            frame: Frame OpenCV ou None
            
        Returns:
            Frame avec overlay
        """
        if frame is None:
            # Créer frame noire avec message
            frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
            cv2.putText(frame, "En attente du flux video...", 
                       (50, self.video_height // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            return frame
        
        # Cloner pour ne pas modifier l'original
        display_frame = frame.copy()
        
        # IA: Traitement de la frame (segmentation, détection, parking)
        ai_info = {}
        if self.enable_ai and self.ai_inference is not None:
            try:
                display_frame, ai_info = self.ai_inference.process_frame(display_frame)
            except Exception as e:
                self.logger.error(f"Erreur inférence IA: {e}")
        
        # Overlay: État du contrôle
        overlay_h = 120
        overlay = np.zeros((overlay_h, display_frame.shape[1], 3), dtype=np.uint8)
        overlay[:, :] = (40, 40, 40)  # Fond gris foncé
        
        # Texte throttle
        throttle_text = f"Throttle: {self.throttle:+.2f}"
        color_throttle = (0, 255, 0) if self.throttle > 0 else (0, 0, 255) if self.throttle < 0 else (200, 200, 200)
        cv2.putText(overlay, throttle_text, (20, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_throttle, 2)
        
        # Barre throttle
        bar_x = 20
        bar_y = 50
        bar_w = 300
        bar_h = 20
        cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), -1)
        throttle_fill = int((self.throttle + 1.0) / 2.0 * bar_w)
        cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + throttle_fill, bar_y + bar_h), color_throttle, -1)
        
        # Texte steering
        steering_text = f"Steering: {self.steering:+.2f}"
        color_steering = (255, 100, 0)
        cv2.putText(overlay, steering_text, (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_steering, 2)
        
        # Barre steering
        bar_y = 100
        cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), -1)
        steering_center = bar_x + bar_w // 2
        steering_pos = steering_center + int(self.steering * bar_w // 2)
        cv2.rectangle(overlay, (steering_center - 2, bar_y), (steering_center + 2, bar_y + bar_h), (255, 255, 255), -1)
        cv2.circle(overlay, (steering_pos, bar_y + bar_h // 2), 12, color_steering, -1)
        
        # FPS
        fps_text = f"FPS: {self.current_fps}"
        cv2.putText(overlay, fps_text, (display_frame.shape[1] - 150, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Statut IA
        if self.enable_ai and ai_info:
            y_offset = 60
            # Objets détectés
            if 'objects' in ai_info:
                obj_count = len(ai_info['objects'])
                cv2.putText(overlay, f"Objets: {obj_count}", 
                           (display_frame.shape[1] - 150, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                y_offset += 20
            
            # Places de parking
            if 'parking_spots' in ai_info:
                spot_count = len(ai_info['parking_spots'])
                if spot_count > 0:
                    cv2.putText(overlay, f"Parking: {spot_count}", 
                               (display_frame.shape[1] - 150, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    y_offset += 20
            
            # Temps inférence
            if 'inference_time_ms' in ai_info:
                inf_time = ai_info['inference_time_ms']
                cv2.putText(overlay, f"AI: {inf_time:.1f}ms", 
                           (display_frame.shape[1] - 150, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
        
        # Statut connexion
        video_status = "VIDEO: ✓" if self.video_receiver.is_connected() else "VIDEO: ✗"
        color_status = (0, 255, 0) if self.video_receiver.is_connected() else (0, 0, 255)
        cv2.putText(overlay, video_status, (display_frame.shape[1] - 150, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_status, 1)
        
        # Combiner overlay avec frame
        display_frame = np.vstack([display_frame, overlay])
        
        return display_frame
    
    def _render_lidar_view(self, points: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        Génère une vue "top-down" du lidar.
        
        Args:
            points: Liste de (angle, distance, confidence)
            
        Returns:
            Image OpenCV
        """
        # Créer canvas noir
        canvas = np.zeros((self.lidar_size, self.lidar_size, 3), dtype=np.uint8)
        
        # Centre de la vue
        center_x = self.lidar_size // 2
        center_y = self.lidar_size // 2
        
        # Échelle: 1 pixel = 1cm, max 3m de rayon
        max_range_mm = 3000  # 3 mètres
        scale = (self.lidar_size // 2 - 20) / max_range_mm
        
        # Dessiner grille circulaire
        for radius_m in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
            radius_px = int(radius_m * 1000 * scale)
            cv2.circle(canvas, (center_x, center_y), radius_px, (50, 50, 50), 1)
            # Label distance
            label = f"{radius_m}m"
            cv2.putText(canvas, label, (center_x + radius_px - 25, center_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)
        
        # Axes
        cv2.line(canvas, (center_x, 0), (center_x, self.lidar_size), (50, 50, 50), 1)
        cv2.line(canvas, (0, center_y), (self.lidar_size, center_y), (50, 50, 50), 1)
        
        # Dessiner points lidar
        for angle_deg, dist_mm, confidence in points:
            # Filtrer points trop loin ou invalides
            if dist_mm <= 0 or dist_mm > max_range_mm:
                continue
            
            # Conversion polaire → cartésien
            # Angle 0° = devant, rotation horaire
            angle_rad = np.radians(angle_deg)
            x = dist_mm * np.sin(angle_rad)
            y = -dist_mm * np.cos(angle_rad)  # -Y car OpenCV Y vers bas
            
            # Projection sur canvas
            px = int(center_x + x * scale)
            py = int(center_y + y * scale)
            
            # Vérifier dans les limites
            if 0 <= px < self.lidar_size and 0 <= py < self.lidar_size:
                # Couleur selon confidence (0-255)
                intensity = int(confidence) if confidence > 0 else 200
                color = (intensity, intensity, intensity)
                cv2.circle(canvas, (px, py), 2, color, -1)
        
        # Dessiner robot au centre (triangle pointant vers le haut)
        robot_points = np.array([
            [center_x, center_y - 15],      # Avant
            [center_x - 10, center_y + 10], # Arrière gauche
            [center_x + 10, center_y + 10]  # Arrière droite
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [robot_points], (0, 255, 0))
        
        # Info
        info_text = f"Points: {len(points)}"
        cv2.putText(canvas, info_text, (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Stats
        stats = self.lidar_receiver.get_stats()
        stats_text = f"Packets: {stats['packets_received']}"
        cv2.putText(canvas, stats_text, (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return canvas
    
    def _render_help_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Ajoute une aide des contrôles sur la frame.
        
        Args:
            frame: Frame à modifier
            
        Returns:
            Frame avec aide
        """
        help_lines = [
            "CONTROLES:",
            "Z/S: Throttle +/-",
            "Q/D: Steering G/D",
            "X: Neutre",
            "ESPACE: Urgence",
            "K: Klaxon",
            "1-4: Sons",
            "+/-: Vitesse max",
            "M: Mode masque IA",
            "H: Aide",
            "ESC/Echap: Quitter"
        ]
        
        y_offset = 30
        for i, line in enumerate(help_lines):
            cv2.putText(frame, line, (frame.shape[1] - 220, y_offset + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return frame
    
    def _update_fps(self):
        """Met à jour le calcul du FPS."""
        self.fps_counter += 1
        elapsed = time.time() - self.last_fps_time
        
        if elapsed >= 1.0:
            self.current_fps = int(self.fps_counter / elapsed)
            self.fps_counter = 0
            self.last_fps_time = time.time()
    
    def run(self):
        """
        Boucle principale du dashboard.
        Affiche vidéo, lidar et gère le contrôle clavier.
        """
        self.logger.info("=== Dashboard en cours d'exécution ===")
        self.logger.info("Appuyez sur H pour afficher l'aide")
        self.logger.info("Appuyez sur ESC ou Echap pour quitter")
        
        show_help = True
        
        while self.running:
            try:
                # === AFFICHAGE VIDÉO ===
                video_frame = self.video_receiver.get_latest_frame()
                display_video = self._render_video_frame(video_frame)
                
                # Aide optionnelle
                if show_help:
                    display_video = self._render_help_overlay(display_video)
                
                cv2.imshow(self.window_video, display_video)
                
                # === AFFICHAGE LIDAR ===
                lidar_points = self.lidar_receiver.get_latest_points()
                lidar_view = self._render_lidar_view(lidar_points)
                cv2.imshow(self.window_lidar, lidar_view)
                
                # === TRAITEMENT CLAVIER ===
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC uniquement
                    self.logger.info("Arrêt demandé")
                    break
                
                elif key == ord('h') or key == ord('H'):
                    # Toggle aide
                    show_help = not show_help
                
                elif key != 255:  # Touche pressée
                    self._process_keyboard(key)
                
                # Mise à jour FPS
                self._update_fps()
                
                # Log périodique
                if int(time.time()) % 10 == 0 and self.fps_counter == 0:
                    self._log_stats()
                
            except KeyboardInterrupt:
                self.logger.info("Interruption détectée")
                break
            except Exception as e:
                self.logger.error(f"Erreur dans boucle principale: {e}")
                time.sleep(0.1)
        
        self.stop()
    
    def _log_stats(self):
        """Affiche les statistiques périodiques."""
        video_stats = self.video_receiver.get_stats()
        lidar_stats = self.lidar_receiver.get_stats()
        controller_stats = self.controller_sender.get_stats()
        
        self.logger.info("=== Statistiques ===")
        self.logger.info(f"Video: {video_stats['frames_received']} frames, "
                        f"{video_stats['bytes_received'] / 1024 / 1024:.1f} MB")
        self.logger.info(f"Lidar: {lidar_stats['packets_received']} packets, "
                        f"{lidar_stats['points_count']} points")
        self.logger.info(f"Controller: {controller_stats['messages_sent']} messages, "
                        f"throttle={controller_stats['current_throttle']:.2f}, "
                        f"steering={controller_stats['current_steering']:.2f}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Robocar Dashboard - Station de contrôle PC"
    )
    parser.add_argument(
        '--robot-ip',
        default='10.84.106.222',
        help='Adresse IP du robot (défaut: 10.84.106.222)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Niveau de log (défaut: INFO)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Désactiver les fonctionnalités IA (segmentation, détection, parking)'
    )
    
    args = parser.parse_args()
    
    # Configurer logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Créer et démarrer dashboard
    dashboard = RobocarDashboard(robot_ip=args.robot_ip, enable_ai=not args.no_ai)
    
    if dashboard.start():
        try:
            dashboard.run()
        except KeyboardInterrupt:
            print("\n🛑 Interruption détectée")
    else:
        print("❌ Erreur de démarrage")
        sys.exit(1)
    
    print("✅ Dashboard arrêté proprement")


if __name__ == "__main__":
    main()
