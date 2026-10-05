"""
SmartFit - Integrated Fitness Monitoring System Backend API
Integrates:
1. Smart Knee Band (ESP32, MPU6050 x2/3, Flex Sensor, FSR x2/4, Li-ion Battery, Vibration Motor)
2. Smart Chest Belt (ESP32, AD8232 ECG, MAX30102, MPU6050, Li-ion Battery)
3. Multimodal Random Forest Exercise Classifier (Scikit-Learn)
4. Integrated NIH OAI Clinical Screening Engine
5. WebSocket Real-Time Telemetry Streaming
"""

import asyncio
import base64
import hashlib
import hmac
import json
import math
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import (
    get_db, init_db, hash_password, verify_password,
    SECRET, TOKEN_EXPIRY_SECONDS
)
from ml.classifier_service import ai_service
from ml.feature_extractor import (
    extract_features_from_buffer, assess_movement_form, compute_knee_angle
)

app = FastAPI(
    title="SmartFit – Integrated Fitness Monitoring System",
    description="Real-time multi-sensor wearable monitoring and AI-based assessment for fitness, sports, rehabilitation, and OA screening.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

STAFF_USER = os.getenv("SMARTFIT_STAFF_USER", "healthcare")
STAFF_PASSWORD = os.getenv("SMARTFIT_STAFF_PASSWORD", "ChangeMe123!")

# Global state for device connections and real-time buffers
device_state = {
    "knee_band": {
        "connected": False,
        "last_seen": 0,
        "battery_pct": 0,
        "firmware": "SmartKneeBand-ESP32-v1.0",
        "mac_address": "AA:BB:CC:DD:EE:01",
        "sensors": {
            "mpu6050_thigh": "OK",
            "mpu6050_shin": "OK",
            "flex_sensor": "OK",
            "fsr_heel": "OK",
            "fsr_forefoot": "OK",
            "vibration_motor": "IDLE"
        }
    },
    "chest_belt": {
        "connected": False,
        "last_seen": 0,
        "battery_pct": 0,
        "firmware": "SmartCardiacBelt-ESP32-v1.0",
        "mac_address": "AA:BB:CC:DD:EE:02",
        "sensors": {
            "ad8232_ecg": "OK",
            "leads_off_plus": False,
            "leads_off_minus": False,
            "max30102": "OK",
            "mpu6050_chest": "OK"
        }
    },
    "simulation_mode": False
}

# In-memory sliding telemetry buffers for real-time feature extraction
knee_buffer: List[Dict[str, Any]] = []
chest_buffer: List[Dict[str, Any]] = []
BUFFER_MAX_SIZE = 100

connected_websockets: List[WebSocket] = []

@app.on_event("startup")
def on_startup():
    init_db()
    print("SmartFit API server started. Database & Models loaded.")

def generate_token(role: str, subject: str) -> str:
    now = int(time.time())
    body = f"{role}:{subject}:{now}"
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode((body + "|" + sig).encode()).decode()

def auth(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization token required")
    try:
        raw = base64.urlsafe_b64decode(authorization[7:].encode()).decode()
        body, sig = raw.rsplit("|", 1)
    except Exception:
        raise HTTPException(401, "Malformed session token")

    expected_sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        raise HTTPException(401, "Tampered or invalid session signature")

    parts = body.split(":", 2)
    if len(parts) < 3:
        raise HTTPException(401, "Invalid token payload format")
    role, subject, issued_at = parts[0], parts[1], int(parts[2])

    if time.time() - issued_at > TOKEN_EXPIRY_SECONDS:
        raise HTTPException(401, "Session has expired. Please log in again.")

    return {"role": role, "subject": subject}

def staff_only(a=Depends(auth)):
    if a["role"] != "staff":
        raise HTTPException(403, "Staff/clinician access required")
    return a

# ----------------- SCHEMAS -----------------
class LoginReq(BaseModel):
    username: str
    password: str

class PatientCreate(BaseModel):
    name: str = Field(min_length=1)
    contact: str
    place: str
    age: int = Field(ge=1, le=120)
    gender: str
    height: float = Field(gt=0)
    weight: float = Field(gt=0)
    pain_side: str

class ScreeningCreate(BaseModel):
    patient_id: str
    knee_angle_mean: float
    knee_angle_range: float
    knee_angle_std: float
    flex_mean: float
    flex_variability: float
    heel_pressure: float
    forefoot_pressure: float
    pressure_imbalance: float
    movement_variability: float
    duration_seconds: int = Field(ge=1)
    data_quality: Optional[str] = "GOOD"
    quality_metrics: Optional[Dict[str, Any]] = None

class CalibrationCreate(BaseModel):
    patient_id: str
    zero_offset_deg: float
    flex_baseline_adc: Optional[int] = None
    heel_tare_adc: Optional[int] = None
    forefoot_tare_adc: Optional[int] = None
    operator_notes: Optional[str] = ""

class ExerciseSessionCreate(BaseModel):
    patient_id: str
    exercise_name: str
    rep_count: int = 0
    duration_seconds: int = 0
    form_score: float = 0.0
    knee_rom: float = 0.0
    avg_heart_rate: float = 0.0
    avg_spo2: float = 0.0
    features: Dict[str, Any]
    classification_result: Dict[str, Any]
    notes: Optional[str] = ""

class TelemetryPacket(BaseModel):
    source: str  # "knee_band" or "chest_belt"
    timestamp: Optional[int] = None
    payload: Dict[str, Any]

class VibrationCommand(BaseModel):
    intensity: int = Field(ge=1, le=10, default=5)
    duration_ms: int = Field(ge=100, le=3000, default=600)
    reason: Optional[str] = "Form correction cue"

# ----------------- SYSTEM ENDPOINTS -----------------
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "system_name": "SmartFit – Integrated Fitness Monitoring System",
        "prototype_disclaimer": "Student/Research Prototype — Real-time multi-sensor assessment. Not a certified medical diagnosis.",
        "rf_model_loaded": ai_service.rf_bundle is not None,
        "oa_model_loaded": ai_service.oa_model is not None,
        "knee_band_status": "Connected" if device_state["knee_band"]["connected"] else "Not Connected",
        "chest_belt_status": "Connected" if device_state["chest_belt"]["connected"] else "Not Connected",
        "simulation_mode": device_state["simulation_mode"]
    }

@app.get("/api/hardware/spec")
def hardware_specification():
    """
    Returns the exact hardware and sensor inventory strictly adhering to Biomedfinix2.pptx.
    """
    return {
        "knee_band": {
            "name": "Smart Knee Band",
            "microcontroller": "ESP32 Dual-Core 240MHz",
            "communication": "ESP-NOW (ESP32-to-ESP32) + WebSocket",
            "sensors": [
                {"name": "MPU6050 6-DOF IMU (Thigh)", "role": "Thigh kinematic tilt, angular velocity & acceleration"},
                {"name": "MPU6050 6-DOF IMU (Shin)", "role": "Shin movement and relative angle differential"},
                {"name": "Flex Sensor", "role": "Direct anatomical joint flexion & bending measurement"},
                {"name": "FSR (Heel & Forefoot)", "role": "Plantar pressure distribution and impact load"},
                {"name": "Vibration Motor", "role": "Haptic biofeedback for wrong movement & abnormal posture alert"}
            ],
            "power": "3.7V Rechargeable Li-ion Battery"
        },
        "chest_belt": {
            "name": "Smart Chest Belt",
            "microcontroller": "ESP32 Dual-Core 240MHz",
            "communication": "ESP-NOW (ESP32-to-ESP32) + WebSocket",
            "sensors": [
                {"name": "AD8232 ECG Sensor", "role": "Analog biopotential biometrics & cardiac rhythm monitoring"},
                {"name": "MAX30102 Pulse Oximeter", "role": "Photoplethysmography (PPG), Heart Rate & SpO2 blood oxygen"},
                {"name": "MPU6050 6-DOF IMU", "role": "Trunk posture, thoracic motion & kinetic activity"}
            ],
            "power": "3.7V Rechargeable Li-ion Battery"
        },
        "architecture": {
            "layer_1": "Sensor Layer (AD8232, MAX30102, MPU6050s, Flex Sensor, FSRs, Vibration Motor)",
            "layer_2": "Signal Conditioning & Pre-processing (Filtering, noise removal, time alignment)",
            "layer_3": "Processing Unit (ESP32 Nodes with ESP-NOW wireless link)",
            "layer_4": "Local Real-Time Communication (WebSocket server, offline-first)",
            "layer_5": "AI/ML Multimodal Data Fusion (Random Forest exercise classifier + OAI clinical model)",
            "layer_6": "User Interface & Biofeedback (React + Vite Web Dashboard + Haptic alert)"
        }
    }

# ----------------- AUTH ENDPOINTS -----------------
@app.post("/api/auth/staff/login")
def staff_login(req: LoginReq):
    if not (hmac.compare_digest(req.username, STAFF_USER) and hmac.compare_digest(req.password, STAFF_PASSWORD)):
        raise HTTPException(401, "Invalid healthcare clinician credentials")
    return {"token": generate_token("staff", STAFF_USER), "role": "staff"}

@app.post("/api/auth/patient/login")
def patient_login(req: LoginReq):
    conn = get_db()
    row = conn.execute("SELECT * FROM patients WHERE username=?", (req.username,)).fetchone()
    conn.close()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Invalid patient credentials")
    return {
        "token": generate_token("patient", row["patient_id"]),
        "role": "patient",
        "patient_id": row["patient_id"],
        "name": row["name"]
    }

# ----------------- PATIENT ENDPOINTS -----------------
@app.post("/api/patients")
def create_patient(x: PatientCreate, _=Depends(staff_only)):
    clean_name = " ".join(x.name.split())
    contact = "".join(ch for ch in x.contact if ch.isdigit())
    if len(contact) < 4 or len(clean_name) < 2:
        raise HTTPException(400, "Name and contact number are invalid")
    username = clean_name.lower().replace(" ", "_")
    password = contact[:4] + clean_name[:2]
    pid = "SF-" + str(int(time.time() * 1000))[-6:]
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO patients VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, clean_name, username, hash_password(password), contact, x.place, x.age, x.gender, x.height, x.weight, x.pain_side, time.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(409, f"Patient could not be registered: {str(e)}")
    return {"patient_id": pid, "username": username, "initial_password": password, "name": clean_name}

@app.get("/api/patients")
def list_patients():
    conn = get_db()
    rows = conn.execute(
        "SELECT patient_id,name,username,contact,place,age,gender,height,weight,pain_side,created_at FROM patients ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/patients/{pid}")
def get_patient(pid: str, a=Depends(auth)):
    if a["role"] == "patient" and a["subject"] != pid:
        raise HTTPException(403, "Unauthorized access to patient record")
    conn = get_db()
    row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Patient record not found")
    return dict(row)

# ----------------- OA SCREENING (PRESERVED OA LOGIC) -----------------
@app.post("/api/screenings")
def create_screening(s: ScreeningCreate, a=Depends(staff_only)):
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE patient_id=?", (s.patient_id,)).fetchone()
    if not patient:
        conn.close()
        raise HTTPException(404, "Patient record not found")

    clinical_result = ai_service.compute_oa_clinical_risk(dict(patient))

    # Retrieve previous screenings for baseline comparison
    prev_screenings = conn.execute(
        "SELECT id, created_at, features_json FROM screenings WHERE patient_id=? ORDER BY id ASC",
        (s.patient_id,)
    ).fetchall()

    baseline_comparison = {}
    if prev_screenings:
        first_features = json.loads(prev_screenings[0]["features_json"])
        delta_rom = round(s.knee_angle_range - (first_features.get("knee_angle_range") or 0), 1)
        delta_imbalance = round(s.pressure_imbalance - (first_features.get("pressure_imbalance") or 0), 1)
        baseline_comparison = {
            "has_baseline": True,
            "baseline_session_id": prev_screenings[0]["id"],
            "baseline_date": prev_screenings[0]["created_at"],
            "baseline_rom": first_features.get("knee_angle_range", 0),
            "current_rom": s.knee_angle_range,
            "delta_rom_deg": delta_rom,
            "delta_imbalance": delta_imbalance
        }
    else:
        baseline_comparison = {
            "has_baseline": False,
            "note": "This screening establishes the patient baseline for longitudinal progression tracking."
        }

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    features_dict = s.model_dump()
    quality_json = json.dumps(s.quality_metrics or {"rating": s.data_quality})
    result_json = json.dumps(clinical_result)
    baseline_json = json.dumps(baseline_comparison)

    conn.execute("""
        INSERT INTO screenings (
            patient_id, created_at, data_quality, firmware_version, model_version,
            features_json, result_json, quality_json, baseline_comparison_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        s.patient_id, now, s.data_quality or "GOOD", "v3.0",
        clinical_result.get("model_version", "OAI-LogReg-v2.1"),
        json.dumps(features_dict), result_json, quality_json, baseline_json
    ))
    conn.commit()
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return {
        "screening_id": sid,
        "patient_id": s.patient_id,
        "created_at": now,
        "data_quality": s.data_quality,
        "features": features_dict,
        "result": clinical_result,
        "baseline_comparison": baseline_comparison
    }

@app.get("/api/patients/{pid}/screenings")
def list_patient_screenings(pid: str, a=Depends(auth)):
    conn = get_db()
    rows = conn.execute(
        """SELECT id, created_at, data_quality, firmware_version, model_version,
                  features_json, result_json, quality_json, baseline_comparison_json
           FROM screenings WHERE patient_id=? ORDER BY created_at DESC""",
        (pid,)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "data_quality": r["data_quality"],
            "firmware_version": r["firmware_version"],
            "model_version": r["model_version"],
            "features": json.loads(r["features_json"]),
            "result": json.loads(r["result_json"]),
            "quality_metrics": json.loads(r["quality_json"] or "{}"),
            "baseline_comparison": json.loads(r["baseline_comparison_json"] or "{}")
        })
    return results

@app.post("/api/calibrations")
def create_calibration(cal: CalibrationCreate, _=Depends(staff_only)):
    conn = get_db()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute("""
        INSERT INTO calibrations (patient_id, created_at, zero_offset_deg, flex_baseline_adc, heel_tare_adc, forefoot_tare_adc, operator_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cal.patient_id, now, cal.zero_offset_deg, cal.flex_baseline_adc, cal.heel_tare_adc, cal.forefoot_tare_adc, cal.operator_notes))
    conn.commit()
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": cid, "patient_id": cal.patient_id, "created_at": now, "zero_offset_deg": cal.zero_offset_deg}

@app.get("/api/patients/{pid}/calibrations")
def get_patient_calibrations(pid: str, a=Depends(auth)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM calibrations WHERE patient_id=? ORDER BY created_at DESC", (pid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- SMARTFIT EXERCISE & ML SESSIONS -----------------
@app.post("/api/ml/classify-live")
def classify_live_telemetry():
    """
    Extracts features from the current sliding telemetry buffer and runs the Random Forest model.
    """
    if not knee_buffer and not chest_buffer:
        return {
            "status": "WAITING_FOR_SENSOR",
            "message": "No live sensor data available in the buffer. Connect wearable device to classify.",
            "exercise_name": "No Data",
            "confidence": 0.0,
            "probabilities": {},
            "rep_count": 0,
            "form": {"status": "No Signal", "form_score": 0.0, "warnings": []}
        }

    feat_result = extract_features_from_buffer(knee_buffer, chest_buffer)
    rf_result = ai_service.classify_exercise(feat_result["vector"])
    form_result = assess_movement_form(feat_result["features"], rf_result.get("exercise_name", ""))

    return {
        "status": "ANALYSIS_COMPLETE",
        "exercise_name": rf_result.get("exercise_name", "Resting / Standing"),
        "confidence": rf_result.get("confidence", 0.0),
        "probabilities": rf_result.get("probabilities", {}),
        "rep_count": feat_result["rep_count"],
        "features": feat_result["features"],
        "form": form_result,
        "model_details": {
            "model_version": rf_result.get("model_version"),
            "algorithm": rf_result.get("algorithm"),
            "disclaimer": rf_result.get("disclaimer")
        }
    }

@app.post("/api/exercise-sessions")
def save_exercise_session(session: ExerciseSessionCreate, _=Depends(staff_only)):
    conn = get_db()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    sid = "SES-" + str(int(time.time() * 1000))[-8:]
    dev_status = {
        "knee_band": device_state["knee_band"]["connected"],
        "chest_belt": device_state["chest_belt"]["connected"]
    }

    conn.execute("""
        INSERT INTO exercise_sessions (
            session_id, patient_id, created_at, exercise_name, rep_count,
            duration_seconds, form_score, knee_rom, avg_heart_rate, avg_spo2,
            device_status_json, features_json, classification_result_json, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sid, session.patient_id, now, session.exercise_name, session.rep_count,
        session.duration_seconds, session.form_score, session.knee_rom,
        session.avg_heart_rate, session.avg_spo2, json.dumps(dev_status),
        json.dumps(session.features), json.dumps(session.classification_result),
        session.notes or ""
    ))
    conn.commit()
    conn.close()

    return {"session_id": sid, "status": "SAVED", "created_at": now}

@app.get("/api/patients/{pid}/exercise-sessions")
def list_patient_exercise_sessions(pid: str, a=Depends(auth)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM exercise_sessions WHERE patient_id=? ORDER BY created_at DESC",
        (pid,)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "session_id": r["session_id"],
            "patient_id": r["patient_id"],
            "created_at": r["created_at"],
            "exercise_name": r["exercise_name"],
            "rep_count": r["rep_count"],
            "duration_seconds": r["duration_seconds"],
            "form_score": r["form_score"],
            "knee_rom": r["knee_rom"],
            "avg_heart_rate": r["avg_heart_rate"],
            "avg_spo2": r["avg_spo2"],
            "device_status": json.loads(r["device_status_json"] or "{}"),
            "features": json.loads(r["features_json"] or "{}"),
            "classification_result": json.loads(r["classification_result_json"] or "{}"),
            "notes": r["notes"]
        })
    return results

# ----------------- DEVICE & TELEMETRY CONTROLS -----------------
@app.get("/api/device/status")
def get_device_status():
    return device_state

@app.post("/api/device/set-connection")
def set_device_connection(device: str, connected: bool):
    """
    Allows user or hardware bridge to update connection state.
    """
    if device in device_state:
        device_state[device]["connected"] = connected
        device_state[device]["last_seen"] = int(time.time()) if connected else 0
        if connected:
            device_state[device]["battery_pct"] = 92
        else:
            device_state[device]["battery_pct"] = 0
        return {"status": "UPDATED", "device": device, "connected": connected}
    raise HTTPException(400, "Unknown device identifier")

@app.post("/api/device/vibration-trigger")
def trigger_vibration(cmd: VibrationCommand):
    """
    Sends vibration alert cue to the Knee Band ESP32 (Vibration Motor).
    Triggered when form deviation or abnormal angle is detected.
    """
    device_state["knee_band"]["sensors"]["vibration_motor"] = "VIBRATING"
    # Schedule motor to return to idle after duration
    asyncio.create_task(reset_vibration(cmd.duration_ms / 1000.0))
    return {
        "status": "COMMAND_SENT",
        "target": "Smart Knee Band (Vibration Motor)",
        "duration_ms": cmd.duration_ms,
        "intensity": cmd.intensity,
        "reason": cmd.reason
    }

async def reset_vibration(delay_s: float):
    await asyncio.sleep(delay_s)
    device_state["knee_band"]["sensors"]["vibration_motor"] = "IDLE"

@app.post("/api/device/simulation-toggle")
def toggle_simulation(enabled: bool):
    """
    Enables/disables laboratory hardware simulation mode for testing when physical sensors are not attached.
    Clearly marked in UI as 'Simulation Mode' vs 'Physical Wearables'.
    """
    device_state["simulation_mode"] = enabled
    device_state["knee_band"]["connected"] = enabled
    device_state["chest_belt"]["connected"] = enabled
    if enabled:
        device_state["knee_band"]["battery_pct"] = 94
        device_state["chest_belt"]["battery_pct"] = 88
    else:
        device_state["knee_band"]["battery_pct"] = 0
        device_state["chest_belt"]["battery_pct"] = 0
        knee_buffer.clear()
        chest_buffer.clear()
    return {"simulation_mode": enabled}

@app.post("/api/telemetry/ingest")
async def ingest_telemetry(pkt: TelemetryPacket):
    """
    Receives live sensor telemetry broadcast from physical ESP32 via HTTP/WebSocket.
    """
    src = pkt.source
    now_ts = int(time.time())
    if src == "knee_band":
        device_state["knee_band"]["connected"] = True
        device_state["knee_band"]["last_seen"] = now_ts
        knee_buffer.append(pkt.payload)
        if len(knee_buffer) > BUFFER_MAX_SIZE:
            knee_buffer.pop(0)
    elif src == "chest_belt":
        device_state["chest_belt"]["connected"] = True
        device_state["chest_belt"]["last_seen"] = now_ts
        chest_buffer.append(pkt.payload)
        if len(chest_buffer) > BUFFER_MAX_SIZE:
            chest_buffer.pop(0)

    # Broadcast to all open WebSockets
    msg = json.dumps({"type": "telemetry", "source": src, "data": pkt.payload})
    for ws in connected_websockets:
        try:
            await ws.send_text(msg)
        except Exception:
            pass

    return {"status": "INGESTED", "source": src}

# ----------------- COMPREHENSIVE REPORT GENERATION -----------------
@app.get("/api/reports/summary/{patient_id}")
def generate_summary_report(patient_id: str):
    conn = get_db()
    pat_row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
    if not pat_row:
        conn.close()
        raise HTTPException(404, "Patient not found")

    patient = dict(pat_row)

    # OA Screenings
    screenings = conn.execute(
        "SELECT * FROM screenings WHERE patient_id=? ORDER BY created_at DESC",
        (patient_id,)
    ).fetchall()

    # Exercise sessions
    sessions = conn.execute(
        "SELECT * FROM exercise_sessions WHERE patient_id=? ORDER BY created_at DESC",
        (patient_id,)
    ).fetchall()

    # Calibrations
    calibrations = conn.execute(
        "SELECT * FROM calibrations WHERE patient_id=? ORDER BY created_at DESC",
        (patient_id,)
    ).fetchall()

    conn.close()

    # Latest OA result
    latest_oa = json.loads(screenings[0]["result_json"]) if screenings else ai_service.compute_oa_clinical_risk(patient)

    # Latest exercise summary
    latest_exercise = None
    if sessions:
        r = sessions[0]
        latest_exercise = {
            "session_id": r["session_id"],
            "created_at": r["created_at"],
            "exercise_name": r["exercise_name"],
            "rep_count": r["rep_count"],
            "duration_seconds": r["duration_seconds"],
            "form_score": r["form_score"],
            "knee_rom": r["knee_rom"],
            "avg_heart_rate": r["avg_heart_rate"],
            "avg_spo2": r["avg_spo2"],
            "features": json.loads(r["features_json"] or "{}"),
            "classification_result": json.loads(r["classification_result_json"] or "{}")
        }

    return {
        "report_id": f"REP-{patient_id}-{int(time.time())}",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "patient": {
            "patient_id": patient["patient_id"],
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "height": patient["height"],
            "weight": patient["weight"],
            "place": patient["place"],
            "contact": patient["contact"],
            "pain_side": patient["pain_side"]
        },
        "device_specifications": hardware_specification(),
        "device_status": device_state,
        "oa_clinical_result": latest_oa,
        "latest_exercise_result": latest_exercise,
        "total_screenings_count": len(screenings),
        "total_exercise_sessions_count": len(sessions),
        "disclaimer": "SmartFit is a research and clinical screening demonstration prototype (SIH26213). It does not provide certified medical diagnoses. All clinical decisions must be confirmed by qualified medical professionals."
    }

# ----------------- REAL-TIME WEBSOCKET STREAM -----------------
@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    print(f"WebSocket client connected. Total clients: {len(connected_websockets)}")

    sim_tick = 0
    try:
        while True:
            # Check for incoming client messages (e.g. toggle commands)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.08)
                msg = json.loads(data)
                if msg.get("action") == "toggle_simulation":
                    toggle_simulation(msg.get("enabled", False))
                elif msg.get("action") == "trigger_vibration":
                    device_state["knee_band"]["sensors"]["vibration_motor"] = "VIBRATING"
                    asyncio.create_task(reset_vibration(0.6))
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass

            sim_tick += 1

            # Prepare telemetry payload
            packet = {
                "timestamp": int(time.time() * 1000),
                "knee_band": {
                    "connected": device_state["knee_band"]["connected"],
                    "battery": device_state["knee_band"]["battery_pct"],
                    "vibration_motor": device_state["knee_band"]["sensors"]["vibration_motor"],
                    "data": None
                },
                "chest_belt": {
                    "connected": device_state["chest_belt"]["connected"],
                    "battery": device_state["chest_belt"]["battery_pct"],
                    "data": None
                },
                "ai_live": None
            }

            # If simulation mode is active (for dev demonstration without physical hardware)
            if device_state["simulation_mode"]:
                # Generates mathematical squat/flexion kinematics
                phase = (sim_tick % 100) / 100.0  # 4-second cycle
                squat_curve = math.sin(phase * 2 * math.pi)

                # Knee kinematics
                current_knee_angle = round(165.0 - max(0, squat_curve) * 75.0, 1)
                flex_val = round(15.0 + max(0, squat_curve) * 65.0, 1)
                heel_p = round(55.0 + squat_curve * 15.0, 1)
                forefoot_p = round(50.0 + max(0, squat_curve) * 35.0, 1)

                knee_data = {
                    "knee_angle": current_knee_angle,
                    "flex_sensor": flex_val,
                    "heel_pressure": heel_p,
                    "forefoot_pressure": forefoot_p,
                    "pressure_imbalance": round(abs(heel_p - forefoot_p) / (heel_p + forefoot_p + 1e-4) * 100, 1),
                    "thigh_accel": round(9.8 + math.sin(phase * 4 * math.pi) * 2.1, 2),
                    "shin_accel": round(9.8 + math.cos(phase * 4 * math.pi) * 1.8, 2),
                    "status": "RECEIVING_DATA"
                }
                packet["knee_band"]["data"] = knee_data
                knee_buffer.append(knee_data)
                if len(knee_buffer) > BUFFER_MAX_SIZE:
                    knee_buffer.pop(0)

                # Chest kinematics & biopotentials
                # ECG synthetic lead-II QRS morphology for continuous waveform
                ecg_val = 2048 + int(math.sin(sim_tick * 0.4) * 120)
                # QRS spike
                if sim_tick % 20 in [0, 1]:
                    ecg_val += 850 if sim_tick % 20 == 0 else -400

                hr_val = round(74.0 + (1.0 - squat_curve) * 12.0, 1)
                spo2_val = 98.5

                chest_data = {
                    "ecg_raw": ecg_val,
                    "heart_rate": hr_val,
                    "spo2": spo2_val,
                    "accel_x": round(0.1 + math.sin(phase * 2 * math.pi) * 1.2, 2),
                    "accel_y": round(0.2 + math.cos(phase * 2 * math.pi) * 0.8, 2),
                    "accel_z": round(9.7 + math.sin(phase * 2 * math.pi) * 1.5, 2),
                    "trunk_tilt": round(12.0 + max(0, squat_curve) * 24.0, 1),
                    "leads_off": False,
                    "status": "RECEIVING_DATA"
                }
                packet["chest_belt"]["data"] = chest_data
                chest_buffer.append(chest_data)
                if len(chest_buffer) > BUFFER_MAX_SIZE:
                    chest_buffer.pop(0)

                # Periodic AI inference
                if sim_tick % 10 == 0 and len(knee_buffer) > 10:
                    feats = extract_features_from_buffer(knee_buffer, chest_buffer)
                    rf_res = ai_service.classify_exercise(feats["vector"])
                    form_res = assess_movement_form(feats["features"], rf_res.get("exercise_name", ""))
                    packet["ai_live"] = {
                        "exercise_name": rf_res.get("exercise_name", "Squats"),
                        "confidence": rf_res.get("confidence", 0.0),
                        "probabilities": rf_res.get("probabilities", {}),
                        "rep_count": feats["rep_count"],
                        "form_score": form_res.get("form_score", 85.0),
                        "form_status": form_res.get("status", "Optimal Form"),
                        "vibration_alert": form_res.get("vibration_alert", False),
                        "warnings": form_res.get("warnings", [])
                    }

            else:
                # PHYSICAL HARDWARE OR DISCONNECTED MODE
                # If physical devices are sending data to buffer, use the latest
                if device_state["knee_band"]["connected"] and knee_buffer:
                    latest_k = knee_buffer[-1]
                    packet["knee_band"]["data"] = {**latest_k, "status": "RECEIVING_DATA"}
                else:
                    packet["knee_band"]["data"] = {
                        "status": "NOT_CONNECTED",
                        "message": "Waiting for Smart Knee Band (ESP32 / ESP-NOW)"
                    }

                if device_state["chest_belt"]["connected"] and chest_buffer:
                    latest_c = chest_buffer[-1]
                    packet["chest_belt"]["data"] = {**latest_c, "status": "RECEIVING_DATA"}
                else:
                    packet["chest_belt"]["data"] = {
                        "status": "NOT_CONNECTED",
                        "message": "Waiting for Smart Chest Belt (ESP32 / AD8232 / MAX30102)"
                    }

            await websocket.send_text(json.dumps(packet))
            await asyncio.sleep(0.06)  # ~16-17 Hz update rate for high performance

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
