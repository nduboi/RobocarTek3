"""
controller_sender.py

Envoyeur de commandes de contrôle vers le robot.
Protocole: UDP JSON avec encode_control_message
"""

import socket
import threading
import logging
import time
from typing import Optional, List, Dict, Any
from protocol_client import encode_control_message, create_heartbeat_message


class ControllerSender:
    """
    Envoie les commandes de contrôle au robot via UDP.
    Thread-safe avec heartbeat automatique.
    """
    
    def __init__(self, robot_ip: str, port: int = 5000, 
                 source_id: str = "pc_dashboard",
                 heartbeat_interval: float = 0.2):
        """
        Initialise l'envoyeur de commandes.
        
        Args:
            robot_ip: Adresse IP du robot
            port: Port UDP de contrôle (défaut: 5000)
            source_id: Identifiant de ce client
            heartbeat_interval: Intervalle de heartbeat en secondes (défaut: 0.2s = 5Hz)
        """
        self.robot_ip = robot_ip
        self.port = port
        self.source_id = source_id
        self.heartbeat_interval = heartbeat_interval
        
        # Socket
        self.socket: Optional[socket.socket] = None
        
        # État du contrôle
        self.throttle = 0.0
        self.steering = 0.0
        self.control_lock = threading.Lock()
        
        # Commandes en attente
        self.pending_commands: List[str] = []
        self.commands_lock = threading.Lock()
        
        # État
        self.running = False
        self.send_thread: Optional[threading.Thread] = None
        
        # Séquence
        self.sequence = 0
        
        # Statistiques
        self.messages_sent = 0
        self.errors_count = 0
        self.last_send_time = 0
        
        # Logging
        self.logger = logging.getLogger('ControllerSender')
    
    def start(self) -> bool:
        """
        Démarre l'envoi de commandes.
        
        Returns:
            True si démarrage réussi
        """
        if self.running:
            self.logger.warning("ControllerSender déjà démarré")
            return False
        
        # Créer socket UDP
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.logger.info(f"Socket UDP créé pour {self.robot_ip}:{self.port}")
        except Exception as e:
            self.logger.error(f"Erreur création socket: {e}")
            return False
        
        self.running = True
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        
        self.logger.info("ControllerSender démarré")
        return True
    
    def stop(self):
        """Arrête l'envoi de commandes."""
        self.logger.info("Arrêt du ControllerSender...")
        self.running = False
        
        # Envoyer arrêt d'urgence avant de fermer
        try:
            self.send_command("emergency_stop")
            time.sleep(0.1)
        except:
            pass
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=2.0)
        
        self.logger.info("ControllerSender arrêté")
    
    def set_control(self, throttle: float, steering: float):
        """
        Définit les valeurs de contrôle à envoyer.
        
        Args:
            throttle: Puissance moteur (-1.0 à 1.0)
            steering: Direction (-1.0 à 1.0)
        """
        with self.control_lock:
            self.throttle = max(-1.0, min(1.0, throttle))
            self.steering = max(-1.0, min(1.0, steering))
    
    def send_command(self, command: str):
        """
        Ajoute une commande ponctuelle à envoyer.
        
        Args:
            command: Commande (ex: "horn", "emergency_stop")
        """
        with self.commands_lock:
            self.pending_commands.append(command)
    
    def _send_message(self, message: str) -> bool:
        """
        Envoie un message au robot.
        
        Args:
            message: Message JSON encodé
            
        Returns:
            True si envoi réussi
        """
        try:
            self.socket.sendto(
                message.encode('utf-8'),
                (self.robot_ip, self.port)
            )
            self.messages_sent += 1
            self.last_send_time = time.time()
            return True
        except Exception as e:
            self.logger.error(f"Erreur envoi: {e}")
            self.errors_count += 1
            return False
    
    def _send_loop(self):
        """Boucle principale d'envoi (thread)."""
        self.logger.info("Thread d'envoi de commandes démarré")
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # Récupérer état actuel
                with self.control_lock:
                    throttle = self.throttle
                    steering = self.steering
                
                # Récupérer commandes
                with self.commands_lock:
                    commands = self.pending_commands.copy()
                    self.pending_commands.clear()
                
                # Déterminer si on doit envoyer
                should_send = False
                
                # Envoyer si commandes en attente
                if commands:
                    should_send = True
                
                # Envoyer si contrôle actif (throttle ou steering non nul)
                if abs(throttle) > 0.001 or abs(steering) > 0.001:
                    should_send = True
                
                # Heartbeat si pas d'activité
                time_since_last = time.time() - last_heartbeat
                if time_since_last >= self.heartbeat_interval:
                    if not should_send:
                        # Envoyer heartbeat
                        msg = create_heartbeat_message(
                            source=self.source_id,
                            sequence=self.sequence
                        )
                        self._send_message(msg)
                        self.sequence += 1
                    
                    last_heartbeat = time.time()
                
                # Envoyer message de contrôle
                if should_send:
                    msg = encode_control_message(
                        source=self.source_id,
                        throttle=throttle,
                        steering=steering,
                        commands=commands if commands else None,
                        sequence=self.sequence
                    )
                    self._send_message(msg)
                    self.sequence += 1
                    last_heartbeat = time.time()
                
                # Fréquence d'envoi: 20Hz (50ms)
                time.sleep(0.05)
                
            except Exception as e:
                self.logger.error(f"Erreur dans boucle d'envoi: {e}")
                self.errors_count += 1
                time.sleep(0.1)
        
        self.logger.info("Thread d'envoi de commandes terminé")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'envoi."""
        with self.control_lock:
            current_throttle = self.throttle
            current_steering = self.steering
        
        return {
            'messages_sent': self.messages_sent,
            'errors': self.errors_count,
            'current_throttle': current_throttle,
            'current_steering': current_steering,
            'last_send_time': self.last_send_time
        }
