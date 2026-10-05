"""
Smart Cardiac Chest Belt - Physiological Vitals Processor
Computes real-time, average, minimum, and maximum parameters for Heart Rate,
RR Interval, and Body Temperature with threshold alarm monitoring.
"""

import time
from typing import Dict, Any, Optional, List

import config


class VitalSignTracker:
    """
    Tracks and aggregates physiological parameters:
    Heart Rate (BPM), RR Interval (ms), and Body Temperature (°C).
    """

    def __init__(self):
        self.reset()
        self.last_alert_times: Dict[str, float] = {}

    def reset(self):
        """Resets all metrics and statistics for a new monitoring session."""
        self.current_hr: Optional[float] = None
        self.hr_values: List[float] = []

        self.current_rr: Optional[float] = None
        self.rr_values: List[float] = []

        self.current_temp: Optional[float] = None
        self.temp_values: List[float] = []

        self.current_spo2: Optional[float] = None

        self.last_alert_times = {}

    def update(self, hr: Optional[float],
               rr: Optional[float],
               temp: Optional[float],
               spo2: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Updates trackers with real incoming sensor values.
        Returns a list of newly triggered alert dicts (if thresholds are exceeded).
        """
        now = time.time()
        new_alerts: List[Dict[str, Any]] = []

        # 1. Update Heart Rate
        if hr is not None and hr > 0:
            self.current_hr = round(float(hr), 1)
            self.hr_values.append(self.current_hr)

            # Check HR thresholds
            if self.current_hr < config.HEART_RATE_LOW:
                alert = self._create_alert("HEART_RATE", f"Bradycardia detected: {self.current_hr:.0f} BPM (Below {config.HEART_RATE_LOW})", "WARNING", now)
                if alert:
                    new_alerts.append(alert)
            elif self.current_hr > config.HEART_RATE_HIGH:
                alert = self._create_alert("HEART_RATE", f"Tachycardia detected: {self.current_hr:.0f} BPM (Above {config.HEART_RATE_HIGH})", "WARNING", now)
                if alert:
                    new_alerts.append(alert)

        # 2. Update RR Interval
        if rr is not None and rr > 0:
            self.current_rr = round(float(rr), 1)
            self.rr_values.append(self.current_rr)

        # 3. Update Body Temperature
        if temp is not None and temp > 0:
            self.current_temp = round(float(temp), 1)
            self.temp_values.append(self.current_temp)

            # Check Temperature thresholds
            if self.current_temp < config.TEMPERATURE_LOW:
                alert = self._create_alert("TEMPERATURE", f"Abnormal low temperature: {self.current_temp:.1f}°C (Below {config.TEMPERATURE_LOW}°C)", "WARNING", now)
                if alert:
                    new_alerts.append(alert)
            elif self.current_temp > config.TEMPERATURE_HIGH:
                alert = self._create_alert("TEMPERATURE", f"Elevated temperature / fever: {self.current_temp:.1f}°C (Above {config.TEMPERATURE_HIGH}°C)", "WARNING", now)
                if alert:
                    new_alerts.append(alert)

        # 4. Optional SpO2
        if spo2 is not None and spo2 > 0:
            self.current_spo2 = round(float(spo2), 1)

        return new_alerts

    def _create_alert(self, alert_type: str, message: str, severity: str, now: float) -> Optional[Dict[str, Any]]:
        """Debounces duplicate alerts within ALERT_DEBOUNCE_SECONDS."""
        last_t = self.last_alert_times.get(alert_type, 0.0)
        if now - last_t >= config.ALERT_DEBOUNCE_SECONDS:
            self.last_alert_times[alert_type] = now
            return {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": time.strftime("%H:%M:%S")
            }
        return None

    # Statistics properties
    @property
    def avg_hr(self) -> Optional[float]:
        return round(sum(self.hr_values) / len(self.hr_values), 1) if self.hr_values else None

    @property
    def min_hr(self) -> Optional[float]:
        return min(self.hr_values) if self.hr_values else None

    @property
    def max_hr(self) -> Optional[float]:
        return max(self.hr_values) if self.hr_values else None

    @property
    def avg_rr(self) -> Optional[float]:
        return round(sum(self.rr_values) / len(self.rr_values), 1) if self.rr_values else None

    @property
    def min_rr(self) -> Optional[float]:
        return min(self.rr_values) if self.rr_values else None

    @property
    def max_rr(self) -> Optional[float]:
        return max(self.rr_values) if self.rr_values else None

    @property
    def avg_temp(self) -> Optional[float]:
        return round(sum(self.temp_values) / len(self.temp_values), 1) if self.temp_values else None

    @property
    def min_temp(self) -> Optional[float]:
        return min(self.temp_values) if self.temp_values else None

    @property
    def max_temp(self) -> Optional[float]:
        return max(self.temp_values) if self.temp_values else None

    def get_summary_stats(self) -> Dict[str, Any]:
        """Returns consolidated statistical summary."""
        return {
            "current_hr": self.current_hr,
            "avg_hr": self.avg_hr,
            "min_hr": self.min_hr,
            "max_hr": self.max_hr,
            "current_rr": self.current_rr,
            "avg_rr": self.avg_rr,
            "min_rr": self.min_rr,
            "max_rr": self.max_rr,
            "current_temp": self.current_temp,
            "avg_temp": self.avg_temp,
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "current_spo2": self.current_spo2
        }
