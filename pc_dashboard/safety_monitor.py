"""
safety_monitor.py

Moniteur de securite base sur le lidar.
Scanne les zones autour du vehicule et declenche un arret d'urgence
si un obstacle est trop proche dans le cone avant.
"""

import logging
from typing import List, Tuple, Dict


class SafetyMonitor:
    """
    Analyse les points lidar par zones (avant, gauche, droite, arriere).
    Calcule un speed_factor proportionnel pour ralentissement progressif.
    Pas de thread : appele une fois par frame depuis la boucle principale.
    """

    FRONT_CONE_HALF_ANGLE = 30       # degres : cone avant [-30, +30] depuis 0
    EMERGENCY_STOP_DIST_MM = 300     # 30 cm -> arret immediat
    SLOW_DOWN_DIST_MM = 800          # 80 cm -> debut ralentissement
    MIN_CONFIDENCE = 50              # ignorer les points faible confiance

    def __init__(self,
                 emergency_dist_mm: int = 300,
                 slow_down_dist_mm: int = 800):
        self.emergency_dist = emergency_dist_mm
        self.slow_down_dist = slow_down_dist_mm
        self.logger = logging.getLogger('SafetyMonitor')

    def update(self, lidar_points: List[Tuple[float, float, float]]) -> Dict:
        """
        Traite un scan lidar complet.

        Args:
            lidar_points: liste de (angle_deg, distance_mm, confidence)
                          0=avant, 90=droite, 180=arriere, 270=gauche

        Returns:
            dict avec :
              emergency_stop, front_min_mm, left_min_mm, right_min_mm,
              rear_min_mm, speed_factor
        """
        if not lidar_points:
            return {
                'emergency_stop': False,
                'front_min_mm': float('inf'),
                'left_min_mm': float('inf'),
                'right_min_mm': float('inf'),
                'rear_min_mm': float('inf'),
                'speed_factor': 1.0,
            }

        front = self._min_distance_in_arc(lidar_points, 0, self.FRONT_CONE_HALF_ANGLE)
        right = self._min_distance_in_arc(lidar_points, 90, 45)
        rear = self._min_distance_in_arc(lidar_points, 180, 45)
        left = self._min_distance_in_arc(lidar_points, 270, 45)

        # Speed factor proportionnel
        if front <= self.emergency_dist:
            speed_factor = 0.0
        elif front < self.slow_down_dist:
            speed_factor = (front - self.emergency_dist) / (self.slow_down_dist - self.emergency_dist)
        else:
            speed_factor = 1.0

        emergency = front <= self.emergency_dist

        if emergency:
            self.logger.warning(f"EMERGENCY STOP - obstacle avant a {front:.0f}mm")

        return {
            'emergency_stop': emergency,
            'front_min_mm': front,
            'left_min_mm': left,
            'right_min_mm': right,
            'rear_min_mm': rear,
            'speed_factor': speed_factor,
        }

    @staticmethod
    def _min_distance_in_arc(points: List[Tuple[float, float, float]],
                              center_deg: float,
                              half_angle: float) -> float:
        """
        Distance minimum parmi les points dans l'arc [center-half, center+half].
        Gere le wraparound 360. Retourne float('inf') si aucun point valide.
        """
        min_dist = float('inf')
        for angle, dist, conf in points:
            if conf < SafetyMonitor.MIN_CONFIDENCE or dist < 30:
                continue
            diff = (angle - center_deg + 180) % 360 - 180
            if abs(diff) <= half_angle:
                if dist < min_dist:
                    min_dist = dist
        return min_dist
