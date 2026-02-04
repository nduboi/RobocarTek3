"""
autonomous_driver.py

Orchestrateur de conduite autonome.
State machine : IDLE -> CRUISE -> SEARCH_SPOT -> APPROACH -> PARK_MANEUVER -> PARKED
"""

import time
import logging
from enum import Enum
from typing import Optional, Tuple, List, Dict

from safety_monitor import SafetyMonitor
from path_follower import PathFollower
from parking_planner import ParkingPlanner, ParkingManeuverPhase


class AutonomousState(Enum):
    IDLE = "IDLE"
    CRUISE = "CRUISE"
    SEARCH_SPOT = "SEARCH_SPOT"
    APPROACH = "APPROACH"
    PARK_MANEUVER = "PARK_MANEUVER"
    PARKED = "PARKED"


class AutonomousDriver:
    """
    Orchestrateur principal. Cree par le dashboard, appele une fois par frame.
    Retourne (throttle, steering) quand actif, None sinon.
    """

    CRUISE_STABILIZE_TIME = 3.0   # secondes avant de chercher une place
    SEARCH_TIMEOUT = 60.0         # secondes max pour trouver une place

    def __init__(self, ai_inference=None):
        """
        Args:
            ai_inference: instance de AIInference (pour acceder au masque route)
        """
        self.safety = SafetyMonitor()
        self.follower = PathFollower()
        self.planner = ParkingPlanner()
        self.ai_inference = ai_inference
        self.state = AutonomousState.IDLE
        self.active = False
        self._state_start_time = 0.0
        self._last_safety_info: Dict = {}
        self.logger = logging.getLogger('AutonomousDriver')

    def toggle(self) -> bool:
        """Active/desactive le mode autonome. Retourne le nouvel etat."""
        self.active = not self.active
        if self.active:
            self._transition(AutonomousState.IDLE)
            self.follower.reset()
            self.logger.info("Mode autonome ACTIVE")
        else:
            self._transition(AutonomousState.IDLE)
            self.planner.abort_maneuver()
            self.logger.info("Mode autonome DESACTIVE")
        return self.active

    def is_active(self) -> bool:
        return self.active

    def get_state(self) -> AutonomousState:
        return self.state

    def get_status_text(self) -> str:
        """Texte pour l'overlay du dashboard."""
        phase_text = ""
        if self.state == AutonomousState.PARK_MANEUVER:
            phase_text = f" ({self.planner.get_phase().name})"

        safety = self._last_safety_info
        front = safety.get('front_min_mm', float('inf'))
        sf = safety.get('speed_factor', 1.0)
        front_str = f"{front:.0f}mm" if front < 10000 else "clear"

        return f"{self.state.value}{phase_text} | front:{front_str} sf:{sf:.1f}"

    def emergency_stop(self):
        """Force l'arret et desactive le mode autonome."""
        self.active = False
        self._transition(AutonomousState.IDLE)
        self.planner.abort_maneuver()
        self.follower.reset()
        self.logger.warning("EMERGENCY STOP - mode autonome desactive")

    def update(self,
               lidar_points: list,
               ai_info: dict,
               frame=None
               ) -> Optional[Tuple[float, float]]:
        """
        Mise a jour principale, appelee une fois par frame.

        Args:
            lidar_points: depuis lidar_receiver.get_latest_points()
            ai_info: depuis ai_inference.process_frame()
            frame: frame video (non utilise directement)

        Returns:
            (throttle, steering) si actif, None sinon.
        """
        if not self.active:
            return None

        # Toujours executer la securite en premier
        safety_info = self.safety.update(lidar_points if lidar_points else [])
        self._last_safety_info = safety_info

        if safety_info['emergency_stop']:
            self.emergency_stop()
            return (0.0, 0.0)

        # Recuperer le masque route si disponible
        road_mask = None
        if self.ai_inference is not None:
            road_mask = self.ai_inference.get_last_road_mask()

        sf = safety_info['speed_factor']

        # State machine
        if self.state == AutonomousState.IDLE:
            self._transition(AutonomousState.CRUISE)
            return (0.0, 0.0)

        elif self.state == AutonomousState.CRUISE:
            steering, valid = self.follower.compute_steering(road_mask)
            throttle = PathFollower.CRUISE_THROTTLE * sf
            if not valid:
                throttle = 0.0

            elapsed = time.time() - self._state_start_time
            if elapsed > self.CRUISE_STABILIZE_TIME:
                self._transition(AutonomousState.SEARCH_SPOT)

            return (throttle, steering)

        elif self.state == AutonomousState.SEARCH_SPOT:
            steering, valid = self.follower.compute_steering(road_mask)
            throttle = PathFollower.SEARCH_THROTTLE * sf

            # Chercher un gap cote droit
            if lidar_points:
                gap = self.planner.detect_parking_gap(lidar_points)
                if gap is not None:
                    self.planner.start_maneuver(gap)
                    self._transition(AutonomousState.APPROACH)
                    return (throttle, steering if valid else 0.0)

            # Timeout : retour en cruise
            elapsed = time.time() - self._state_start_time
            if elapsed > self.SEARCH_TIMEOUT:
                self.logger.info("Timeout recherche de place, retour en CRUISE")
                self._transition(AutonomousState.CRUISE)

            return (throttle, steering if valid else 0.0)

        elif self.state == AutonomousState.APPROACH:
            throttle, steering, done = self.planner.update_maneuver(
                lidar_points if lidar_points else [], safety_info)

            # Transition quand la phase avance au-dela de ALIGN_ALONGSIDE
            phase = self.planner.get_phase()
            if phase.value >= ParkingManeuverPhase.TURN_INTO_SPOT.value:
                self._transition(AutonomousState.PARK_MANEUVER)

            return (throttle * sf, steering)

        elif self.state == AutonomousState.PARK_MANEUVER:
            throttle, steering, done = self.planner.update_maneuver(
                lidar_points if lidar_points else [], safety_info)

            if done:
                self._transition(AutonomousState.PARKED)

            return (throttle * sf, steering)

        elif self.state == AutonomousState.PARKED:
            return (0.0, 0.0)

        return None

    def _transition(self, new_state: AutonomousState):
        if new_state != self.state:
            self.logger.info(f"Etat: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self._state_start_time = time.time()
