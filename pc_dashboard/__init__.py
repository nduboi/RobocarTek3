"""
Robocar PC Dashboard

Dashboard de pilotage pour robot Robocar.
Interface graphique temps réel avec flux vidéo, lidar et contrôle clavier.
"""

__version__ = "1.0.0"
__author__ = "RobocarTek3 Team"

from .video_receiver import VideoReceiver
from .lidar_receiver import LidarReceiver
from .controller_sender import ControllerSender
from .protocol_client import encode_control_message, create_heartbeat_message

__all__ = [
    'VideoReceiver',
    'LidarReceiver',
    'ControllerSender',
    'encode_control_message',
    'create_heartbeat_message'
]
