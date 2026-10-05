# SMART CARDIAC CHEST BELT
### Real-Time Physiological Monitoring System

> **DISCLAIMER:** *Student/Research Prototype — Not a Medical Diagnostic Device.*

The **Smart Cardiac Chest Belt** is an ESP32-based wearable physiological monitoring system designed for real-time biopotential and kinetic telemetry analysis. It continuously collects biometrical and movement information and visualizes them on a clean, professional Python desktop dashboard.

---

## 1. System Architecture & Complete Data Flow

```
ESP32 + Sensors (AD8232, MAX30102, MPU6050, Temp)
       │
       │  Local Wi-Fi (No Internet Required)
       ▼
WebSocket Server (ws://ESP32_IP:81)
       │
       ▼
Python Desktop Application (Smart Cardiac Chest Belt)
       │
       ├──► Real-Time Signal Processing (SciPy Butterworth Bandpass Filter: 0.5–40 Hz)
       ├──► R-Peak & RR Interval Detection (Heart Rate Fallback Engine)
       ├──► Physiological Threshold Monitoring (Bradycardia, Tachycardia, Fever Alarms)
       ├──► Kinetic & Rule-Based Fall Detection (MPU6050 Composite Magnitude Spikes)
       ├──► Live High-FPS Waveform Plotting (PyQtGraph Rolling Buffer)
       ├──► SQLite Persistence (`data/smartcardiac.db`)
       ├──► Clinical Session Audit Logging
       └──► Publication-Grade PDF Report Compilation (ReportLab) & CSV Data Export
```

---

## 2. Monitored Parameters

1. **Electrocardiogram (ECG):** Analog biopotential from AD8232 single-lead heart rate monitor, passed through a 2nd-order Butterworth IIR bandpass filter (0.5 – 40 Hz).
2. **Heart Rate (BPM):** Optical photoplethysmography via MAX30102 with algorithmic ECG R-peak fallback.
3. **RR Interval (ms):** Cardiac beat-to-beat interval with normative limits (600–1200 ms).
4. **Body Temperature (°C):** Body surface temperature sensor (LM35 / NTC thermistor).
5. **Motion Intensity:** Triaxial accelerometer ($\sqrt{a_x^2 + a_y^2 + a_z^2}$) classified into `LOW` (resting), `NORMAL`, and `HIGH` (active).
6. **Fall Detection:** Sudden kinetic impact detection ($\ge 22.0\text{ m/s}^2$ or $\approx 2.25g$) with immediate visual screen alerts, debouncing, and event logging.
7. **ECG Signal Quality:** Automatic leads-off and rail detection (`GOOD SIGNAL`, `POOR SIGNAL`, `NO SIGNAL`).

---

## 3. Hardware Pinout Configuration

| Component | Sensor Function | ESP32 GPIO Pin | Interface | Important Notes |
| :--- | :--- | :--- | :--- | :--- |
| **AD8232** | Single-Lead ECG | **GPIO 34** | ADC1_CH6 | Analog biopotential output |
| **AD8232 LO+** | Leads-Off Positive | **GPIO 32** | Digital Input | Electrode disconnect sensing |
| **AD8232 LO-** | Leads-Off Negative | **GPIO 33** | Digital Input | Electrode disconnect sensing |
| **Temp Sensor** | Body Surface Temp | **GPIO 35** | ADC1_CH7 | LM35 / NTC thermistor |
| **MPU6050** | 6-DOF Accelerometer | **GPIO 21 (SDA), 22 (SCL)**| I2C (0x68) | Shared I2C bus |
| **MAX30102** | Heart Rate & Pulse Ox | **GPIO 21 (SDA), 22 (SCL)**| I2C (0x57) | Shared I2C bus |

> **IMPORTANT ESP32 ARCHITECTURE RULE:** Only **ADC1** pins (GPIO 32–39) are used for analog sensors. In the ESP32 chip architecture, **ADC2 is hardware-disabled whenever Wi-Fi is actively transmitting**.

---

## 4. Telemetry JSON Packet Format

The ESP32 broadcasts JSON packets across WebSocket (`ws://ESP32_IP:81`):

```json
{
    "type": "sensor_data",
    "timestamp": 123456,
    "ecg": 2048,
    "heart_rate": 78,
    "spo2": 98,
    "temperature": 36.7,
    "accel_x": 0.25,
    "accel_y": 1.02,
    "accel_z": 9.71,
    "gyro_x": 0.04,
    "gyro_y": 0.12,
    "gyro_z": 0.03,
    "fall": false
}
```

The application safely handles missing fields and automatically maintains connection health without crashing if any sensor is disconnected.

---

## 5. Software Structure

```
C:\SmartFit\
│
├── config.py                  # Central configuration (IP, port, thresholds, sampling)
├── main.py                    # Safe entry point (Spyder & interactive kernel compatible)
├── requirements.txt           # Python dependency specifications
├── README.md                  # System manual and hardware documentation
├── test_esp32_simulator.py    # Local standalone WebSocket simulator server
├── validate_project.py        # Automated end-to-end verification suite
│
├── communication/
│   └── websocket_client.py    # Background QThread WebSocket client
│
├── database/
│   └── database.py            # SQLite database manager (smartcardiac.db)
│
├── processing/
│   ├── ecg.py                 # SciPy bandpass filter & QRS peak detector
│   ├── heart_rate.py          # Vitals tracking & physiological threshold alarms
│   └── fall_detection.py      # Triaxial motion magnitude & impact fall detection
│
├── reports/
│   └── report.py              # ReportLab PDF generator & Matplotlib ECG plot builder
│
├── ui/
│   ├── styles.py              # Modern medical light theme stylesheet
│   ├── dashboard.py           # Consolidated primary monitoring window
│   └── main_window.py         # Backward-compatibility alias
│
├── esp32/
│   └── SmartCardiacBelt.ino   # Complete Arduino firmware for ESP32
│
├── data/                      # SQLite database files and CSV exports
└── reports_output/            # Generated PDF clinical session reports
```

---

## 6. Installation & Execution

### 1. Requirements
Install dependencies using pip:
```bash
pip install -r requirements.txt
```

### 2. Running the Desktop Application
```bash
python main.py
```
*(Fully compatible with Spyder and Anaconda without `libshiboken` singleton errors).*

### 3. Testing Without Hardware (Simulator Mode)
If physical ESP32 hardware is not yet attached, launch the built-in simulator in a second terminal:
```bash
python test_esp32_simulator.py
```
In the SmartFit desktop app, set **ESP32 IP** to `127.0.0.1` and click **CONNECT**.
