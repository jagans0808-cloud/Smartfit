# SmartFit – Integrated Fitness Monitoring System
### Real-Time Multi-Sensor Wearable Telemetry & AI-Based Assessment

> **DISCLAIMER:** *Student/Research Prototype (SIH26213) — Real-time multi-sensor wearable assessment. Not a certified medical diagnosis device.*

---

## 1. Overview & Concept

**SmartFit** is an integrated wearable platform uniting two wireless body-worn sensor nodes:
1. **Smart Knee Band** (Kinematics, joint bending, plantar load, and tactile biofeedback)
2. **Smart Chest Belt** (Electrocardiography, photoplethysmography, pulse oximetry, and trunk posture)

The system integrates physiological, motion, joint-angle, and foot-pressure sensing into a wireless two-ESP32 wearable architecture, providing real-time exercise classification, form guidance, and centralized web-based monitoring.

---

## 2. Hardware Inventory (Strictly Biomedfinix2)

### Smart Knee Band
* **ESP32**: Dual-Core microcontroller with ESP-NOW wireless link
* **MPU6050 #1**: Thigh motion, angular velocity & acceleration (I2C `0x68`)
* **MPU6050 #2**: Shin motion & joint angle differential (I2C `0x69`)
* **Flex Sensor**: Anatomical knee joint bending measurement (ADC1 `GPIO 36`)
* **FSR ×2**: Plantar pressure measurement — Heel (`GPIO 39`) & Forefoot (`GPIO 34`)
* **Vibration Motor**: Tactile form correction cue & deviation alert (`GPIO 26`)
* **Li-ion Battery**: 3.7V rechargeable power supply

### Smart Chest Belt
* **ESP32**: Dual-Core Gateway Node (ESP-NOW receiver & WebSocket server)
* **AD8232 ECG**: Analog Lead-II biopotential monitoring (`GPIO 34`, LO+ `GPIO 32`, LO- `GPIO 33`)
* **MAX30102**: Optical PPG for Heart Rate & SpO2 blood oxygen saturation (I2C `0x57`)
* **MPU6050**: Thoracic motion, trunk lean, and posture stability (I2C `0x68`)
* **Li-ion Battery**: 3.7V rechargeable power supply

---

## 3. Technology Stack

* **Frontend**: React 19, Vite 8, Lucide React, HTML5 Canvas / SVG dynamic charting
* **Backend**: Python 3.12, FastAPI, Uvicorn, SQLite3, WebSockets
* **AI / ML**: Python, Scikit-Learn (Random Forest Classifier for movement/exercise classification) + NIH OAI Clinical Reference Logistic Regression Pipeline (Preserved from OA system)
* **Embedded / Firmware**: C++ / Arduino ESP32, ESP-NOW protocol, ArduinoJson, WebSocketsServer

---

## 4. Complete Folder Structure

```
c:\SmartFit\
│
├── backend/
│   ├── .venv/                         # Isolated Python virtual environment
│   ├── data/
│   │   └── smartfit.db                # SQLite database (OA schema + SmartFit sessions)
│   ├── ml/
│   │   ├── train_exercise_rf.py       # Random Forest training script (Scikit-Learn)
│   │   ├── feature_extractor.py       # Multimodal signal processing & feature extraction
│   │   └── classifier_service.py      # Dual AI inference engine (Random Forest + OA Model)
│   ├── models/
│   │   ├── exercise_rf_model.joblib   # Trained Random Forest exercise classifier
│   │   └── oa_model.joblib            # NIH OAI clinical reference model
│   ├── database.py                    # Database models, auth, and SQLite schema
│   ├── main.py                        # FastAPI endpoints and real-time WebSocket server
│   └── requirements.txt               # Backend dependencies
│
├── frontend/
│   ├── dist/                          # Production build output
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx             # Active patient switcher, hardware status & sim toggle
│   │   │   ├── Sidebar.jsx            # System navigation
│   │   │   ├── SensorStatusBadge.jsx  # Status badges (Connected, Receiving, Waiting, etc.)
│   │   │   ├── ECGWaveformChart.jsx   # 60fps medical grid ECG oscilloscope canvas
│   │   │   ├── KneeAngleChart.jsx     # Dynamic knee joint kinematics line chart
│   │   │   ├── PlantarPressureVisualizer.jsx # Foot insole Heel/Forefoot FSR load distribution
│   │   │   ├── JointFlexionGauge.jsx  # Flex Sensor curvature arc gauge
│   │   │   └── MedicalDisclaimer.jsx  # Safety prototype disclaimer notice
│   │   ├── context/
│   │   │   └── SmartFitContext.jsx    # React state & WebSocket telemetry client
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Unified executive dashboard with live metrics
│   │   │   ├── Patients.jsx           # Patient registration, directory, and baseline
│   │   │   ├── KneeBand.jsx           # Smart Knee Band monitoring & OA screening panel
│   │   │   ├── ChestBelt.jsx          # Smart Chest Belt monitoring & Lead-II ECG oscilloscope
│   │   │   ├── CombinedMonitoring.jsx # Synchronized dual-device monitoring & session recording
│   │   │   ├── AIAnalysis.jsx         # Random Forest classification & OA clinical analysis
│   │   │   ├── Reports.jsx            # Publication-grade printable report & JSON export
│   │   │   └── DeviceHardware.jsx     # Hardware pinouts, ESP-NOW architecture & packet inspector
│   │   ├── styles/
│   │   │   └── index.css              # Modern medical dark theme design tokens & print styles
│   │   ├── App.jsx                    # Root application container
│   │   └── main.jsx                   # React DOM entry point
│   ├── index.html                     # Application HTML5 shell
│   ├── package.json                   # Frontend dependencies
│   └── vite.config.js                 # Vite build configuration
│
├── esp32/
│   ├── SmartKneeBand.ino              # Knee Band firmware (Sensors, ESP-NOW transmitter, Haptic cue)
│   └── SmartChestBelt.ino             # Chest Belt firmware (AD8232, MAX30102, ESP-NOW gateway)
│
├── start_backend.bat                  # Starts FastAPI backend (Port 8000)
├── start_frontend.bat                 # Starts React Vite frontend (Port 5173)
├── run_smartfit.bat                   # One-click launcher for full system
└── README_SMARTFIT.md                 # System manual & architecture specification
```

---

## 5. End-to-End Data Flow & Device Communication

```
[Smart Knee Band]
  • MPU6050 Thigh (0x68)
  • MPU6050 Shin  (0x69)
  • Flex Sensor   (GPIO 36)
  • FSR Heel      (GPIO 39)
  • FSR Forefoot  (GPIO 34)
  • Vibration Motor (GPIO 26)
        │
        │ ESP-NOW (Cable-Free, Peer-to-Peer, No Internet Required)
        ▼
[Smart Chest Belt Gateway]
  • AD8232 ECG (GPIO 34) + LO+/- (GPIO 32, 33)
  • MAX30102 PPG (I2C 0x57)
  • MPU6050 Chest (I2C 0x68)
        │
        │ WebSocket Stream (ws://IP:8000/ws/live or ws://ESP32_IP:81)
        ▼
[SmartFit FastAPI Backend Engine]
        │
        ├──► Signal Preprocessing (Noise Filtering, Time-Alignment)
        ├──► Feature Extraction (Angles, ROM, Plantar Balance, HR dynamics)
        ├──► Multimodal Data Fusion
        ├──► Scikit-Learn Random Forest Classifier (Movement/Exercise Prediction)
        ├──► Integrated OAI Clinical Screening Model (Radiographic OA Likelihood)
        ├──► SQLite Persistence (smartfit.db)
        │
        ▼
[SmartFit React Dashboard (Web UI)]
        │
        ├──► Live 60fps ECG Oscilloscope
        ├──► Dynamic Knee Kinematics Line Graph
        ├──► Plantar FSR Insole Visualizer
        ├──► Flex Sensor Curvature Arc Gauge
        ├──► Synchronized Combined Session Recorder
        ├──► Haptic Alert Actuation Control
        └──► Printable Comprehensive Clinical & Fitness Report
```

---

## 6. How the Wearables Connect

### Smart Knee Band Connection
1. The Smart Knee Band powers on via its onboard 3.7V Li-ion battery.
2. The ESP32 initializes Wi-Fi in Station mode and activates **ESP-NOW**.
3. It continuously samples the dual MPU6050 IMUs, Flex sensor ADC, and plantar FSRs at 25 Hz.
4. It broadcasts packed telemetry directly to the Chest Belt Gateway using peer MAC addressing.
5. It listens for incoming haptic trigger bytes (`0xAA`) and activates the vibration motor for form cues.

### Smart Chest Belt Connection
1. The Smart Chest Belt powers on and initializes the AD8232 ECG, MAX30102 PPG, and chest MPU6050.
2. It registers an ESP-NOW receive callback to ingest Knee Band packets.
3. It bundles chest biopotentials with the received knee kinematics into synchronized multimodal JSON packets.
4. It streams packets over local WebSocket to the SmartFit web application.

---

## 7. AI/ML Integration

### Random Forest Exercise Classifier (Scikit-Learn)
* **Model File**: `backend/models/exercise_rf_model.joblib`
* **Input Features**: 12 multimodal kinematic and physiological parameters:
  `knee_angle_mean`, `knee_angle_rom`, `knee_angle_velocity_max`, `flex_sensor_mean`, `heel_pressure_mean`, `forefoot_pressure_mean`, `pressure_heel_forefoot_ratio`, `chest_accel_mag_mean`, `chest_accel_var`, `trunk_tilt_angle`, `heart_rate_bpm`, `cadence_rpm`.
* **Classified Classes**:
  1. `Resting / Standing`
  2. `Squats`
  3. `Lunges`
  4. `Knee Flexion-Extension`
  5. `Walking / Gait`
* **Outputs**: Predicted exercise, confidence probability distribution, repetition count (peak-valley hysteresis), movement form score, and haptic feedback alerts.

### Integrated OA Clinical Reference Model
* **Model File**: `backend/models/oa_model.joblib` (Preserved directly from existing OA system)
* **Predictor Features**: Validated clinical parameters — Age, BMI, and Symptom presence.
* **Separation of Concerns**: The Random Forest model classifies kinetic exercises; the OAI model assesses epidemiological radiographic OA likelihood without claiming the RF model is an OA diagnostic tool.

---

## 8. How to Run the Application Locally

### Step 1: Automated Launch (Recommended)
Double-click `run_smartfit.bat` in the project root:
```bat
c:\SmartFit\run_smartfit.bat
```
This automatically launches:
* **Backend Server**: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`)
* **Frontend Web App**: `http://localhost:5173`

### Step 2: Individual Manual Launch
**Backend**:
```powershell
cd c:\SmartFit\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend**:
```powershell
cd c:\SmartFit\frontend
npm run dev
```

Open your browser to `http://localhost:5173`.
