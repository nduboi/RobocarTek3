"""
lidar_receiver.py

Récepteur UDP pour les données du lidar LD19.
S'enregistre auprès du serveur UDP lidar sur la Jetson.
Protocole: JSON avec fragments {"timestamp", "fragment", "total_fragments", "points": [{"a", "d", "c"}]}
"""

import socket
import json
import threading
import logging
import time
from typing import Optional, List, Tuple, Dict, Any, Callable
from collections import defaultdict


class LidarReceiver:
    """
    Reçoit les points lidar depuis le serveur UDP Jetson.
    S'enregistre auprès du serveur pour que celui-ci sache vers qui envoyer.
    """
    
    def __init__(self, jetson_ip: str = "10.84.106.222", port: int = 15975, 
                 points_callback: Optional[Callable] = None):
        """
        Initialise le récepteur lidar.
        
        Args:
            jetson_ip: Adresse IP de la Jetson (défaut: 10.84.106.222)
            port: Port UDP du serveur lidar (défaut: 15975)
            points_callback: Fonction appelée avec liste de points [(angle, dist, conf), ...]
        """
        self.jetson_ip = jetson_ip
        self.port = port
        self.points_callback = points_callback
        
        # Socket
        self.socket: Optional[socket.socket] = None
        
        # État
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Points lidar (thread-safe)
        self.latest_points: List[Tuple[float, float, float]] = []
        self.points_lock = threading.Lock()
        
        # Reconstruction de fragments
        self.fragments_buffer: Dict[int, List] = defaultdict(list)
        self.last_complete_timestamp = 0
        
        # Statistiques
        self.packets_received = 0
        self.points_received = 0
        self.errors_count = 0
        
        # Logging
        self.logger = logging.getLogger('LidarReceiver')
    
    def start(self) -> bool:
        """
        Démarre la réception lidar.
        
        Returns:
            True si démarrage réussi
        """
        if self.running:
            self.logger.warning("LidarReceiver déjà démarré")
            return False
        
        # Créer socket UDP pour recevoir
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)
            
            self.logger.info(f"Socket UDP lidar: 0.0.0.0:{self.port}")
        except Exception as e:
            self.logger.error(f"Erreur création socket: {e}")
            return False
        
        # Envoyer paquet d'enregistrement au serveur
        try:
            self.socket.sendto(b"REGISTER", (self.jetson_ip, self.port))
            self.logger.info(f"✅ Enregistré auprès du serveur {self.jetson_ip}:{self.port}")
        except Exception as e:
            self.logger.error(f"Erreur enregistrement: {e}")
        
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("LidarReceiver démarré (écoute UDP)")
        return True
    
    def stop(self):
        """Arrête la réception lidar."""
        self.logger.info("Arrêt du LidarReceiver...")
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        self.logger.info("LidarReceiver arrêté")
    
    def get_latest_points(self) -> List[Tuple[float, float, float]]:
        """
        Récupère les derniers points lidar (thread-safe).
        
        Returns:
            Liste de tuples (angle, distance, confidence)
        """
        with self.points_lock:
            return self.latest_points.copy()
    
    def _parse_packet(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse un paquet UDP JSON.
        
        Args:
            data: Données UDP reçues
            
        Returns:
            Dict avec données parsées ou None si erreur
        """
        try:
            json_str = data.decode('utf-8')
            packet = json.loads(json_str)
            return packet
        except Exception as e:
            self.logger.error(f"Erreur parsing JSON: {e}")
            self.errors_count += 1
            return None
    
    def _process_packet(self, packet: Dict[str, Any]):
        """
        Traite un paquet lidar (avec ou sans fragmentation).
        
        Args:
            packet: Paquet parsé
        """
        # Vérifier si fragmenté
        if 'fragment' in packet and 'total_fragments' in packet:
            self._process_fragmented_packet(packet)
        else:
            # Paquet complet direct
            self._extract_points(packet)
    
    def _process_fragmented_packet(self, packet: Dict[str, Any]):
        """
        Reconstruit les points depuis des paquets fragmentés.
        
        Args:
            packet: Paquet fragmenté
        """
        timestamp = packet.get('timestamp', 0)
        fragment_id = packet.get('fragment', 0)
        total_fragments = packet.get('total_fragments', 1)
        
        # Stocker fragment
        self.fragments_buffer[fragment_id] = packet.get('points', [])
        
        # Vérifier si tous les fragments reçus
        if len(self.fragments_buffer) >= total_fragments:
            # Fusionner tous les fragments
            all_points = []
            for i in range(total_fragments):
                if i in self.fragments_buffer:
                    all_points.extend(self.fragments_buffer[i])
            
            # Convertir au format interne (angle, dist, conf)
            points = [
                (p.get('a', 0), p.get('d', 0), p.get('c', 0))
                for p in all_points
            ]
            
            # Stocker points
            with self.points_lock:
                self.latest_points = points
                self.points_received += len(points)
            
            # Callback
            if self.points_callback:
                try:
                    self.points_callback(points)
                except Exception as e:
                    self.logger.error(f"Erreur callback: {e}")
            
            # Nettoyer buffer
            self.fragments_buffer.clear()
            self.last_complete_timestamp = timestamp
    
    def _extract_points(self, packet: Dict[str, Any]):
        """
        Extrait les points d'un paquet non fragmenté.
        
        Args:
            packet: Paquet contenant directement "points" ou "pts"
        """
        # Support pour différents formats
        points_data = packet.get('points') or packet.get('pts')
        
        if not points_data:
            return
        
        # Convertir au format (angle, dist, conf)
        points = []
        for p in points_data:
            if isinstance(p, dict):
                # Format {"a": angle, "d": dist, "c": conf}
                points.append((p.get('a', 0), p.get('d', 0), p.get('c', 0)))
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                # Format [angle, dist, conf]
                conf = p[2] if len(p) > 2 else 255
                points.append((p[0], p[1], conf))
        
        # Stocker
        with self.points_lock:
            self.latest_points = points
            self.points_received += len(points)
        
        # Callback
        if self.points_callback:
            try:
                self.points_callback(points)
            except Exception as e:
                self.logger.error(f"Erreur callback: {e}")
    
    def _receive_loop(self):
        """Boucle principale de réception (thread)."""
        self.logger.info("Thread de réception lidar démarré")
        
        packets_log_count = 0
        
        while self.running:
            try:
                # Recevoir paquet UDP
                data, addr = self.socket.recvfrom(65535)
                self.packets_received += 1
                packets_log_count += 1
                
                # DEBUG: Log au premier paquet et tous les 10
                if packets_log_count == 1 or packets_log_count % 10 == 0:
                    self.logger.debug(f"[RX #{self.packets_received}] {len(data)} bytes de {addr}")
                    if packets_log_count == 1:
                        # Premier paquet: afficher le contenu
                        try:
                            preview = data[:200].decode('utf-8', errors='ignore')
                            self.logger.debug(f"[RX] Aperçu: {preview[:100]}...")
                        except:
                            pass
                
                # Parser (peut contenir plusieurs lignes JSON)
                lines = data.decode('utf-8', errors='ignore').split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            packet = json.loads(line)
                            self._process_packet(packet)
                        except json.JSONDecodeError:
                            continue
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur réception: {e}")
                    self.errors_count += 1
        
        self.logger.info("Thread de réception lidar terminé")
    
    def _connect(self) -> bool:
        """
        Établit la connexion TCP à la Jetson.
        
        Returns:
            True si connexion réussie
        """
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
            
            self.logger.info(f"Connexion à {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.logger.info(f"✅ Connecté au lidar")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur connexion: {e}")
            self.connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de réception."""
        return {
            'packets_received': self.packets_received,
            'points_received': self.points_received,
            'errors': self.errors_count,
            'points_count': len(self.latest_points)
        }
