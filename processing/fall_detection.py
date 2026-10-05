"""
Smart Cardiac Chest Belt - Motion & Fall Detection Module
Calculates triaxial acceleration magnitude, classifies motion level,
and evaluates rule-based impact fall events with debounced alerts.
"""

import time
import math
from typing import Dict, Any, Optional, Tuple

import config


class MotionAndFallDetector:
    """
    Evaluates real MPU6050 accelerometer telemetry.
    Computes composite acceleration magnitude, motion intensity category,
    and detects sudden impact falls.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Resets detector state for a new session."""
        self.fall_count: int = 0
        self.is_fall_active: bool = False
        self.last_fall_time: float = 0.0
        self.last_fall_alert_time: float = 0.0
        self.last_magnitude: float = 9.8
        self.last_level: str = "NORMAL"

    def evaluate(self, ax: Optional[float],
                 ay: Optional[float],
                 az: Optional[float],
                 raw_fall_flag: Optional[bool] = None) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Evaluates accelerometer readings and fall flags.
        Returns:
            (motion_info_dict, optional_fall_alert_dict)
        """
        now = time.time()

        if ax is None or ay is None or az is None:
            return {
                "magnitude": 0.0,
                "level": "NO DATA",
                "fall_status": "NO FALL",
                "fall_count": self.fall_count,
                "is_fall": False,
                "accel_x": None,
                "accel_y": None,
                "accel_z": None
            }, None

        # 1. Composite acceleration magnitude
        magnitude = math.sqrt(ax * ax + ay * ay + az * az)
        self.last_magnitude = round(magnitude, 2)

        # 2. Motion Intensity Level
        # Baseline gravity is ~9.8 m/s^2. Dynamic deviation measures activity:
        deviation = abs(magnitude - 9.8)
        if deviation < config.MOTION_LOW_THRESHOLD:
            level = "LOW"
        elif deviation > config.MOTION_HIGH_THRESHOLD:
            level = "HIGH"
        else:
            level = "NORMAL"
        self.last_level = level

        # 3. Rule-Based Fall Detection
        # Triggers if:
        # a) ESP32 pre-computed fall flag is True
        # b) OR acceleration magnitude exceeds impact spike threshold (FALL_THRESHOLD)
        is_impact_spike = magnitude >= config.FALL_THRESHOLD
        is_hardware_fall = bool(raw_fall_flag)

        fall_event_triggered = False
        alert_dict = None

        if is_impact_spike or is_hardware_fall:
            # Check debounce cooldown period
            if now - self.last_fall_time >= config.FALL_DEBOUNCE_SECONDS:
                self.fall_count += 1
                self.last_fall_time = now
                self.is_fall_active = True
                fall_event_triggered = True

                alert_dict = {
                    "alert_type": "FALL_DETECTED",
                    "message": f"Fall impact detected! Acceleration spike: {magnitude:.1f} m/s²",
                    "severity": "CRITICAL",
                    "timestamp": time.strftime("%H:%M:%S")
                }

        # Keep visual fall alert active for 3 seconds post-impact for clear user visibility
        if self.is_fall_active and (now - self.last_fall_time > 3.5):
            self.is_fall_active = False

        fall_status = "FALL DETECTED" if self.is_fall_active else "NO FALL"

        motion_info = {
            "magnitude": self.last_magnitude,
            "level": level,
            "fall_status": fall_status,
            "fall_count": self.fall_count,
            "is_fall": self.is_fall_active,
            "accel_x": round(ax, 2),
            "accel_y": round(ay, 2),
            "accel_z": round(az, 2)
        }

        return motion_info, alert_dict
