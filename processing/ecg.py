"""
Smart Cardiac Chest Belt - ECG Signal Processing Module
Causal IIR bandpass filtering (0.5 - 40 Hz), signal quality estimation,
R-peak detection, and RR-interval / Heart Rate estimation fallback.
"""

import time
from collections import deque
from typing import Tuple, Optional
import numpy as np
from scipy import signal

import config


class ECGProcessor:
    """
    Processes streaming AD8232 ECG data using digital signal processing.
    Extracts filtered amplitude, signal quality, and fallback RR / HR calculations.
    """

    def __init__(self, sample_rate: int = config.ECG_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.nyquist = 0.5 * sample_rate

        # 2nd-order Butterworth bandpass filter: 0.5 Hz - 40.0 Hz
        low = 0.5 / self.nyquist
        high = 40.0 / self.nyquist
        self.b, self.a = signal.butter(2, [low, high], btype='bandpass')
        self.zi = signal.lfilter_zi(self.b, self.a)

        # Signal buffer for online peak detection (~2 seconds of data)
        self.buffer_len = int(sample_rate * 2.0)
        self.raw_buffer = deque(maxlen=self.buffer_len)
        self.filt_buffer = deque(maxlen=self.buffer_len)
        self.time_buffer = deque(maxlen=self.buffer_len)

        # Peak detection tracking
        self.last_peak_time: Optional[float] = None
        self.last_rr_ms: Optional[float] = None
        self.last_hr_bpm: Optional[float] = None
        self.last_sample_time: float = 0.0

    def reset(self):
        """Resets filter memory and buffers."""
        self.zi = signal.lfilter_zi(self.b, self.a)
        self.raw_buffer.clear()
        self.filt_buffer.clear()
        self.time_buffer.clear()
        self.last_peak_time = None
        self.last_rr_ms = None
        self.last_hr_bpm = None
        self.last_sample_time = 0.0

    def add_sample(self, raw_val: Optional[float],
                   timestamp_ms: Optional[int] = None) -> Tuple[Optional[float], str, Optional[float], Optional[float]]:
        """
        Processes a single incoming ECG sample.
        Returns:
            (filtered_ecg, signal_quality, estimated_hr, estimated_rr_ms)
        """
        now = time.time()

        if raw_val is None:
            # Check if signal has timed out
            if now - self.last_sample_time > 1.5:
                return None, "NO SIGNAL", None, None
            return None, "POOR SIGNAL", self.last_hr_bpm, self.last_rr_ms

        self.last_sample_time = now
        t_sec = (timestamp_ms / 1000.0) if timestamp_ms else now

        # Leads-off / Rail detection (AD8232 outputs near 0 or 4095 if disconnected / railed)
        if raw_val < 50 or raw_val > 4045:
            self.raw_buffer.append(raw_val)
            self.filt_buffer.append(0.0)
            self.time_buffer.append(t_sec)
            return 0.0, "POOR SIGNAL", None, None

        # Apply causal IIR filter
        try:
            filtered_arr, self.zi = signal.lfilter(self.b, self.a, [raw_val], zi=self.zi)
            filtered_val = float(filtered_arr[0])
        except Exception:
            filtered_val = float(raw_val - 2048)

        self.raw_buffer.append(raw_val)
        self.filt_buffer.append(filtered_val)
        self.time_buffer.append(t_sec)

        # Signal Quality Assessment
        quality = "GOOD SIGNAL"
        if len(self.raw_buffer) >= 25:
            # Check variance in recent window
            variance = np.var(list(self.raw_buffer)[-25:])
            if variance < 5.0:
                quality = "NO SIGNAL"
            elif variance > 800000.0:
                quality = "POOR SIGNAL"

        # Online R-Peak & RR Interval Detection
        # Minimum physical distance between consecutive beats: ~300 ms (max 200 BPM)
        min_distance_samples = int(0.32 * self.sample_rate)

        if len(self.filt_buffer) >= int(self.sample_rate * 1.2):
            recent_filt = np.array(self.filt_buffer)
            recent_times = np.array(self.time_buffer)

            # Adaptive dynamic threshold (upper 85th percentile of squared derivative or amplitude)
            std_dev = np.std(recent_filt)
            mean_val = np.mean(recent_filt)
            threshold = mean_val + 1.2 * std_dev

            # Check if newest point is a local peak above threshold
            if len(recent_filt) >= 3 and recent_filt[-2] > threshold:
                if recent_filt[-2] > recent_filt[-3] and recent_filt[-2] >= recent_filt[-1]:
                    peak_time = recent_times[-2]

                    if self.last_peak_time is not None:
                        dt = peak_time - self.last_peak_time
                        rr_ms = dt * 1000.0

                        # Physiological RR range: 300 ms (200 BPM) to 1800 ms (33 BPM)
                        if 300 <= rr_ms <= 1800:
                            self.last_rr_ms = round(rr_ms, 1)
                            self.last_hr_bpm = round(60000.0 / rr_ms, 1)
                            self.last_peak_time = peak_time
                    else:
                        self.last_peak_time = peak_time

        return filtered_val, quality, self.last_hr_bpm, self.last_rr_ms
