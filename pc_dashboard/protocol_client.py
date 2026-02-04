"""
protocol_client.py

Module de protocole pour la station sol (PC).
Basé sur le protocole du serveur Robocar.
"""

import json
import time
from typing import Dict, Any, Optional, List


# --- CONSTANTES ---
PROTOCOL_VERSION = "1.0"


def encode_control_message(
    source: str,
    throttle: float,
    steering: float,
    throttle_max: Optional[float] = None,
    commands: Optional[List[str]] = None,
    sequence: int = 0
) -> str:
    """
    Crée un message de contrôle JSON pour le robot.
    
    Args:
        source: ID du client (ex: "pc_dashboard")
        throttle: Puissance moteur (-1.0 à 1.0)
        steering: Direction (-1.0 à 1.0)
        throttle_max: Puissance maximale optionnelle (0.0 à 0.5)
        commands: Liste de commandes ponctuelles
        sequence: Numéro de séquence du message
        
    Returns:
        Message JSON encodé en string
    """
    # Clamper les valeurs pour sécurité
    throttle = max(-1.0, min(1.0, throttle))
    steering = max(-1.0, min(1.0, steering))
    
    data = {
        'throttle': round(throttle, 3),
        'steering': round(steering, 3)
    }
    
    if throttle_max is not None:
        data['throttle_max'] = max(0.0, min(0.5, throttle_max))
    
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'source': source,
        'type': 'control',
        'data': data,
        'commands': commands or [],
        'sequence': sequence
    }
    
    return json.dumps(message)


def create_heartbeat_message(source: str, sequence: int = 0) -> str:
    """
    Crée un message heartbeat (keep-alive).
    
    Args:
        source: ID du client
        sequence: Numéro de séquence
        
    Returns:
        Message JSON encodé
    """
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'source': source,
        'type': 'heartbeat',
        'sequence': sequence
    }
    
    return json.dumps(message)
