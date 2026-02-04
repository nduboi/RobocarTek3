"""
video_receiver.py

Récepteur vidéo TCP pour le flux caméra du robot.
Protocole: [4 bytes taille big-endian] + [JPEG bytes]
"""

import socket
import struct
import threading
import logging
import time
import cv2
import numpy as np
from typing import Optional, Callable, Dict, Any


class VideoReceiver:
    """
    Reçoit et décode le flux vidéo TCP depuis le robot.
    Thread-safe avec callback pour nouvelles frames.
    """
    
    def __init__(self, robot_ip: str, port: int = 4488, 
                 frame_callback: Optional[Callable] = None):
        """
        Initialise le récepteur vidéo.
        
        Args:
            robot_ip: Adresse IP du robot
            port: Port TCP du flux vidéo (défaut: 4488)
            frame_callback: Fonction appelée à chaque nouvelle frame (frame_array)
        """
        self.robot_ip = robot_ip
        self.port = port
        self.frame_callback = frame_callback
        
        # Socket
        self.socket: Optional[socket.socket] = None
        
        # État
        self.running = False
        self.connected = False
        self.thread: Optional[threading.Thread] = None
        
        # Dernière frame reçue (thread-safe)
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        
        # Statistiques
        self.frames_received = 0
        self.bytes_received = 0
        self.connection_attempts = 0
        
        # Logging
        self.logger = logging.getLogger('VideoReceiver')
    
    def start(self) -> bool:
        """
        Démarre la réception vidéo en thread séparé.
        
        Returns:
            True si démarrage réussi
        """
        if self.running:
            self.logger.warning("VideoReceiver déjà démarré")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        
        self.logger.info(f"VideoReceiver démarré ({self.robot_ip}:{self.port})")
        return True
    
    def stop(self):
        """Arrête la réception vidéo."""
        self.logger.info("Arrêt du VideoReceiver...")
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        self.logger.info("VideoReceiver arrêté")
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Récupère la dernière frame reçue (thread-safe).
        
        Returns:
            Frame numpy array ou None
        """
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def is_connected(self) -> bool:
        """Retourne True si connecté au serveur vidéo."""
        return self.connected
    
    def _connect(self) -> bool:
        """
        Tente de se connecter au serveur vidéo.
        
        Returns:
            True si connexion réussie
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # Timeout connexion
            
            self.logger.info(f"Connexion à {self.robot_ip}:{self.port}...")
            self.socket.connect((self.robot_ip, self.port))
            
            self.socket.settimeout(1.0)  # Timeout lecture
            self.connected = True
            self.connection_attempts += 1
            
            self.logger.info("✅ Connecté au serveur vidéo")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            self.socket = None
            self.connected = False
            return False
    
    def _recv_exact(self, num_bytes: int) -> Optional[bytes]:
        """
        Reçoit exactement num_bytes du socket.
        
        Args:
            num_bytes: Nombre de bytes à recevoir
            
        Returns:
            Bytes reçus ou None si erreur
        """
        data = bytearray()
        while len(data) < num_bytes:
            try:
                chunk = self.socket.recv(num_bytes - len(data))
                if not chunk:
                    return None  # Connexion fermée
                data.extend(chunk)
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Erreur réception: {e}")
                return None
        
        return bytes(data)
    
    def _receive_frame(self) -> Optional[np.ndarray]:
        """
        Reçoit une frame complète du serveur.
        Protocole: [4 bytes taille] + [JPEG data]
        
        Returns:
            Frame décodée ou None si erreur
        """
        # Lire header (4 bytes big-endian)
        header_data = self._recv_exact(4)
        if not header_data:
            return None
        
        # Extraire taille
        msg_size = struct.unpack(">L", header_data)[0]
        
        # Sécurité: limite de taille
        if msg_size > 10 * 1024 * 1024:  # 10 MB max
            self.logger.error(f"Taille de frame invalide: {msg_size}")
            return None
        
        # Lire payload JPEG
        jpeg_data = self._recv_exact(msg_size)
        if not jpeg_data:
            return None
        
        self.bytes_received += msg_size + 4
        
        # Décoder JPEG
        try:
            frame = cv2.imdecode(
                np.frombuffer(jpeg_data, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            return frame
        except Exception as e:
            self.logger.error(f"Erreur décodage JPEG: {e}")
            return None
    
    def _receive_loop(self):
        """Boucle principale de réception (thread)."""
        self.logger.info("Thread de réception vidéo démarré")
        
        while self.running:
            # Connexion si nécessaire
            if not self.connected:
                if not self._connect():
                    time.sleep(2.0)  # Attendre avant retry
                    continue
            
            # Recevoir frame
            frame = self._receive_frame()
            
            if frame is not None:
                self.frames_received += 1
                
                # Stocker frame
                with self.frame_lock:
                    self.latest_frame = frame
                
                # Callback
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        self.logger.error(f"Erreur callback: {e}")
            
            else:
                # Perte de connexion
                self.logger.warning("Perte de connexion vidéo")
                self.connected = False
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                self.socket = None
        
        self.logger.info("Thread de réception vidéo terminé")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de réception."""
        return {
            'connected': self.connected,
            'frames_received': self.frames_received,
            'bytes_received': self.bytes_received,
            'connection_attempts': self.connection_attempts,
            'fps': 0  # À calculer si besoin
        }
