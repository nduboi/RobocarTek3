"""
parking_planner.py

Detection de places de parking par lidar (gaps entre obstacles)
et execution d'une manoeuvre de stationnement en bataille (perpendiculaire).
"""

import math
import time
import logging
from enum import Enum
from typing import List, Tuple, Dict, Optional


class ParkingManeuverPhase(Enum):
    NOT_STARTED = 0
    ALIGN_ALONGSIDE = 1    # avancer le long de la rangee, depasser la place
    TURN_INTO_SPOT = 2     # braquer a fond et entrer dans la place
    STRAIGHTEN = 3         # redresser les roues, continuer tout droit
    FINAL_ADJUST = 4       # petites corrections, arret
    DONE = 5


class ParkingPlanner:
    """
    Detecte les places libres via le lidar (gaps cote droit) et execute
    une manoeuvre de parking en bataille. Pas de thread.
    """

    # Detection de gap
    MIN_GAP_WIDTH_MM = 600       # largeur minimale d'une place (~60cm pour le robot)
    CLOSE_THRESHOLD_MM = 1500    # obstacle proche (voiture garee)
    FAR_THRESHOLD_MM = 2500      # espace libre (pas d'obstacle)
    RIGHT_SCAN_CENTER_DEG = 90
    RIGHT_SCAN_HALF_DEG = 30
    MIN_CONFIDENCE = 50

    # Manoeuvre
    ALONGSIDE_THROTTLE = 0.10
    ALONGSIDE_DURATION = 1.5     # secondes
    PARK_THROTTLE = 0.08
    TURN_STEERING = 0.9          # braquage quasi-max a droite
    TURN_DURATION = 2.0
    STRAIGHTEN_THROTTLE = 0.05
    STRAIGHTEN_DURATION = 1.5
    ADJUST_DURATION = 1.0

    def __init__(self):
        self._phase = ParkingManeuverPhase.NOT_STARTED
        self._phase_start_time = 0.0
        self._detected_gap: Optional[Dict] = None
        self.logger = logging.getLogger('ParkingPlanner')

    def detect_parking_gap(self,
                           lidar_points: List[Tuple[float, float, float]]
                           ) -> Optional[Dict]:
        """
        Scanne le cote droit (60-120 deg) pour trouver un gap entre obstacles.

        Returns:
            dict avec gap_center_deg, gap_width_mm, gap_distance_mm,
            gap_start_deg, gap_end_deg. Ou None si pas de place.
        """
        # Filtrer les points dans l'arc droit
        right_points = []
        for angle, dist, conf in lidar_points:
            if conf < self.MIN_CONFIDENCE or dist < 30:
                continue
            diff = (angle - self.RIGHT_SCAN_CENTER_DEG + 180) % 360 - 180
            if abs(diff) <= self.RIGHT_SCAN_HALF_DEG:
                right_points.append((angle, dist))

        if len(right_points) < 5:
            return None

        # Bucketer par bins de 2 degres, garder la distance min par bin
        right_points.sort(key=lambda p: p[0])
        bins: Dict[float, float] = {}
        for angle, dist in right_points:
            bin_key = round(angle / 2) * 2
            if bin_key not in bins or dist < bins[bin_key]:
                bins[bin_key] = dist

        sorted_bins = sorted(bins.items())
        if len(sorted_bins) < 3:
            return None

        # Trouver transition proche -> loin (debut gap) puis loin -> proche (fin gap)
        gap_start = None
        for i in range(1, len(sorted_bins)):
            prev_angle, prev_dist = sorted_bins[i - 1]
            curr_angle, curr_dist = sorted_bins[i]

            if gap_start is None:
                if prev_dist < self.CLOSE_THRESHOLD_MM and curr_dist > self.FAR_THRESHOLD_MM:
                    gap_start = curr_angle
            else:
                if curr_dist < self.CLOSE_THRESHOLD_MM:
                    gap_end = prev_angle
                    # Calculer la largeur du gap
                    gap_angle_rad = math.radians(gap_end - gap_start)
                    far_dists = [d for a, d in sorted_bins
                                 if gap_start <= a <= gap_end and d > self.FAR_THRESHOLD_MM]
                    if far_dists:
                        mean_dist = sum(far_dists) / len(far_dists)
                        gap_width = gap_angle_rad * mean_dist

                        if gap_width > self.MIN_GAP_WIDTH_MM:
                            return {
                                'gap_center_deg': (gap_start + gap_end) / 2,
                                'gap_width_mm': gap_width,
                                'gap_distance_mm': mean_dist,
                                'gap_start_deg': gap_start,
                                'gap_end_deg': gap_end,
                            }
                    gap_start = None

        return None

    def start_maneuver(self, gap: Dict):
        """Demarrer une manoeuvre de parking pour le gap donne."""
        self._detected_gap = gap
        self._set_phase(ParkingManeuverPhase.ALIGN_ALONGSIDE)
        self.logger.info(f"Manoeuvre demarree - gap a {gap['gap_center_deg']:.0f} deg, "
                        f"largeur {gap['gap_width_mm']:.0f}mm")

    def abort_maneuver(self):
        """Annuler la manoeuvre en cours."""
        self._phase = ParkingManeuverPhase.NOT_STARTED
        self._detected_gap = None
        self.logger.info("Manoeuvre annulee")

    def is_maneuvering(self) -> bool:
        return self._phase not in (ParkingManeuverPhase.NOT_STARTED,
                                   ParkingManeuverPhase.DONE)

    def get_phase(self) -> ParkingManeuverPhase:
        return self._phase

    def update_maneuver(self,
                        lidar_points: List[Tuple[float, float, float]],
                        safety_info: Dict
                        ) -> Tuple[float, float, bool]:
        """
        Execute une etape de la manoeuvre de parking.

        Returns:
            (throttle, steering, maneuver_complete)
        """
        elapsed = time.time() - self._phase_start_time

        if self._phase == ParkingManeuverPhase.ALIGN_ALONGSIDE:
            # Avancer tout droit pour depasser la place
            if elapsed > self.ALONGSIDE_DURATION or safety_info.get('right_min_mm', 0) > 2000:
                self._set_phase(ParkingManeuverPhase.TURN_INTO_SPOT)
            return self.ALONGSIDE_THROTTLE, 0.0, False

        elif self._phase == ParkingManeuverPhase.TURN_INTO_SPOT:
            # Braquer a droite et entrer dans la place
            if elapsed > self.TURN_DURATION or safety_info.get('front_min_mm', float('inf')) < 600:
                self._set_phase(ParkingManeuverPhase.STRAIGHTEN)
            return self.PARK_THROTTLE, self.TURN_STEERING, False

        elif self._phase == ParkingManeuverPhase.STRAIGHTEN:
            # Redresser et avancer dans la place
            if elapsed > self.STRAIGHTEN_DURATION or safety_info.get('front_min_mm', float('inf')) < 400:
                self._set_phase(ParkingManeuverPhase.FINAL_ADJUST)
            return self.STRAIGHTEN_THROTTLE, 0.0, False

        elif self._phase == ParkingManeuverPhase.FINAL_ADJUST:
            # Arret et ajustement final
            if elapsed > self.ADJUST_DURATION:
                self._set_phase(ParkingManeuverPhase.DONE)
            return 0.0, 0.0, False

        elif self._phase == ParkingManeuverPhase.DONE:
            return 0.0, 0.0, True

        return 0.0, 0.0, False

    def _set_phase(self, phase: ParkingManeuverPhase):
        self.logger.info(f"Phase parking: {self._phase.name} -> {phase.name}")
        self._phase = phase
        self._phase_start_time = time.time()
