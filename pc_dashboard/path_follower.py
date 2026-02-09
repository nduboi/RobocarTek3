"""
path_follower.py

Suivi de voie par PID base sur le masque de segmentation route.
Calcule le centroide de la route dans la partie basse de l'image
et corrige la direction via un controleur PID.
"""

import numpy as np
import time
import logging
from typing import Optional, Tuple


class PathFollower:
    """
    Calcule une commande steering a partir du masque de segmentation route.
    Pas de thread : appele une fois par frame.
    """

    CRUISE_THROTTLE = 0.15
    SEARCH_THROTTLE = 0.10
    MIN_ROAD_PIXELS = 100  # minimum de pixels route pour considerer la detection valide

    def __init__(self,
                 kp: float = 1.5,
                 ki: float = 0.0,
                 kd: float = 0.3):
        """
        Args:
            kp, ki, kd: gains PID pour la correction de direction
        """
        self._kp = kp
        self._ki = ki
        self._kd = kd
        self._prev_error = 0.0
        self._integral = 0.0
        self._last_time = time.time()
        self.logger = logging.getLogger('PathFollower')

    def compute_steering(self, road_mask: Optional[np.ndarray]) -> Tuple[float, bool]:
        """
        Calcule le steering a partir du masque de segmentation route.

        Args:
            road_mask: masque binaire (0 ou 255) de la meme taille que la frame video.
                       None si pas de segmentation disponible.

        Returns:
            (steering, valid):
              steering: float [-1.0, 1.0] (negatif=gauche, positif=droite)
              valid: True si la route a ete detectee et le steering est fiable
        """
        if road_mask is None:
            return 0.0, False

        h, w = road_mask.shape[:2]

        # Prendre seulement le bas 40% de l'image (zone proche, plus pertinente)
        roi = road_mask[int(h * 0.6):, :]
        ys, xs = np.where(roi > 0)

        if len(xs) < self.MIN_ROAD_PIXELS:
            return 0.0, False

        centroid_x = float(np.mean(xs))
        image_center = w / 2.0

        # Erreur normalisee : positif = route a droite -> braquer a droite
        error = (centroid_x - image_center) / (w / 2.0)

        now = time.time()
        dt = now - self._last_time
        if dt <= 0:
            dt = 0.05

        # PID
        p = self._kp * error
        self._integral = max(-0.3, min(0.3, self._integral + self._ki * error * dt))
        i = self._integral
        d = self._kd * (error - self._prev_error) / dt if dt > 0 else 0.0

        steering = max(-1.0, min(1.0, p + i + d))

        self._prev_error = error
        self._last_time = now

        return steering, True

    def reset(self):
        """Reinitialise l'etat du PID."""
        self._prev_error = 0.0
        self._integral = 0.0
        self._last_time = time.time()
