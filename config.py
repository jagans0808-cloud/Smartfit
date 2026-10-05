"""
Smart Cardiac Chest Belt - System Configuration
Centralized configuration parameters, network targets, physiological alarm limits,
motion thresholds, and storage locations.
"""

import os

# Base directory for relative file paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Data & Storage Directories
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_OUTPUT_DIR = os.path.join(BASE_DIR, "reports_output")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)

# SQLite Database Location
DATABASE_PATH = os.path.join(DATA_DIR, "smartcardiac.db")

# Network Defaults
DEFAULT_ESP32_IP = "192.168.1.105"
WEBSOCKET_PORT = 81
WEBSOCKET_TIMEOUT_S = 5.0
AUTO_RECONNECT_INTERVAL_S = 3.0

# Biomedical Sampling & Waveform Display
ECG_SAMPLE_RATE = 250          # Samples per second (Hz)
MAX_GRAPH_POINTS = 750         # 3.0-second rolling window at 250 Hz
GRAPH_REFRESH_RATE_MS = 40     # ~25 FPS GUI rendering loop

# Physiological Alarm Limits
HEART_RATE_LOW = 50            # Bradycardia warning threshold (BPM)
HEART_RATE_HIGH = 120          # Tachycardia warning threshold (BPM)
RR_INTERVAL_MIN_MS = 450       # Low RR warning (tachycardia)
RR_INTERVAL_MAX_MS = 1250      # High RR warning (bradycardia)

TEMPERATURE_LOW = 35.0         # Hypothermia warning (°C)
TEMPERATURE_HIGH = 38.0        # Hyperthermia / fever warning (°C)

# Motion & Fall Detection Parameters
# Composite acceleration magnitude = sqrt(ax^2 + ay^2 + az^2)
# Baseline resting gravity is ~9.8 m/s^2 (or ~1.0 g)
# Dynamic motion deviation = |magnitude - 9.8|
MOTION_LOW_THRESHOLD = 0.8     # Below this is considered LOW motion (resting)
MOTION_HIGH_THRESHOLD = 3.5    # Above this is HIGH motion (running / vigorous)

# Fall Detection Rule:
# Sudden acceleration magnitude spike exceeding threshold (e.g. impact >= 22.0 m/s^2 or ~2.25g)
FALL_THRESHOLD = 22.0          # m/s^2 impact spike threshold
FALL_DEBOUNCE_SECONDS = 3.0    # Minimum cooldown between consecutive fall events
ALERT_DEBOUNCE_SECONDS = 2.0   # Cooldown for duplicate alert messages

# Project Presentation Information
PROJECT_TITLE = "SMART CARDIAC CHEST BELT"
PROJECT_SUBTITLE = "Real-Time Physiological Monitoring System"
PROJECT_DISCLAIMER = "Student/Research Prototype — Not a Medical Diagnostic Device"
