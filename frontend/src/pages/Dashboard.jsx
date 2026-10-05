import React from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "../components/SensorStatusBadge";
import ECGWaveformChart from "../components/ECGWaveformChart";
import KneeAngleChart from "../components/KneeAngleChart";
import PlantarPressureVisualizer from "../components/PlantarPressureVisualizer";
import MedicalDisclaimer from "../components/MedicalDisclaimer";
import { 
  Activity, Heart, Battery, Zap, Shield, FileText, 
  Layers, Cpu, ArrowUpRight, Vibrate, CheckCircle2
} from "lucide-react";

export default function Dashboard({ setActiveTab }) {
  const { 
    activePatient, kneeState, chestState, 
    aiLive, ecgBuffer, kneeAngleBuffer,
    triggerVibration
  } = useSmartFit();

  const isKneeReceiving = kneeState.status === "RECEIVING_DATA";
  const isChestReceiving = chestState.status === "RECEIVING_DATA";

  const bmi = activePatient ? (activePatient.weight / ((activePatient.height / 100) ** 2)).toFixed(1) : "—";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Patient & System Header Banner */}
      <div className="card" style={{
        background: "var(--banner-bg)",
        border: "1px solid var(--border-color)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>
                {activePatient ? activePatient.name : "Select Patient"}
              </h2>
              <span className="badge badge-connected" style={{ textTransform: "none" }}>
                {activePatient?.patient_id}
              </span>
            </div>
            <div style={{ fontSize: "0.825rem", color: "var(--text-secondary)", marginTop: "0.25rem", display: "flex", gap: "1.2rem", flexWrap: "wrap" }}>
              <span>Age: <strong>{activePatient?.age || "—"} yrs</strong></span>
              <span>Gender: <strong>{activePatient?.gender || "—"}</strong></span>
              <span>Height: <strong>{activePatient?.height || "—"} cm</strong></span>
              <span>Weight: <strong>{activePatient?.weight || "—"} kg</strong></span>
              <span>BMI: <strong style={{ color: "var(--accent-cyan)" }}>{bmi} kg/m²</strong></span>
              <span>Reported Pain: <strong>{activePatient?.pain_side || "None"}</strong></span>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
            <button 
              className="btn btn-cyan"
              onClick={() => setActiveTab("combined")}
            >
              <Layers size={15} />
              Combined Monitoring
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => setActiveTab("reports")}
            >
              <FileText size={15} />
              View Report
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => triggerVibration(6, 600, "Dashboard Form Cue")}
              title="Send haptic cue to Knee Band vibration motor"
            >
              <Vibrate size={15} style={{ color: "var(--accent-amber)" }} />
              Test Vibration
            </button>
          </div>
        </div>
      </div>

      {/* Live Parameter Grid (6 Key Metrics) */}
      <div className="grid-3">
        {/* 1. Knee Angle */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Live Knee Angle</span>
            <SensorStatusBadge status={kneeState.status} />
          </div>
          <div className="stat-value" style={{ color: "var(--accent-cyan)" }}>
            {isKneeReceiving && kneeState.knee_angle !== null ? `${kneeState.knee_angle}` : "—"}
            <span className="stat-unit">deg</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isKneeReceiving ? "Dual MPU6050 + Flex Sensor fusion" : "Waiting for Sensor"}
          </div>
        </div>

        {/* 2. Heart Rate */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Heart Rate (ECG/PPG)</span>
            <SensorStatusBadge status={chestState.status} />
          </div>
          <div className="stat-value" style={{ color: "var(--accent-rose)" }}>
            {isChestReceiving && chestState.heart_rate !== null ? `${chestState.heart_rate}` : "—"}
            <span className="stat-unit">BPM</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isChestReceiving ? "AD8232 Lead-II & MAX30102" : "Waiting for Sensor"}
          </div>
        </div>

        {/* 3. Blood Oxygen SpO2 */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Pulse Oximetry (SpO2)</span>
            <SensorStatusBadge status={chestState.status} />
          </div>
          <div className="stat-value" style={{ color: "var(--accent-emerald)" }}>
            {isChestReceiving && chestState.spo2 !== null ? `${chestState.spo2}` : "—"}
            <span className="stat-unit">%</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isChestReceiving ? "MAX30102 Optical Sensor" : "Waiting for Sensor"}
          </div>
        </div>

        {/* 4. Plantar Pressure Balance */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Plantar Balance (FSR)</span>
            <SensorStatusBadge status={kneeState.status} />
          </div>
          <div className="stat-value" style={{ color: "var(--accent-blue)" }}>
            {isKneeReceiving && kneeState.heel_pressure !== null && kneeState.forefoot_pressure !== null
              ? `${Math.round(kneeState.heel_pressure)} / ${Math.round(kneeState.forefoot_pressure)}`
              : "—"}
            <span className="stat-unit">H/F %</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isKneeReceiving ? "Heel vs Forefoot Load" : "Waiting for Sensor"}
          </div>
        </div>

        {/* 5. Trunk Posture Lean */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Trunk Posture Tilt</span>
            <SensorStatusBadge status={chestState.status} />
          </div>
          <div className="stat-value" style={{ color: "var(--accent-amber)" }}>
            {isChestReceiving && chestState.trunk_tilt !== null ? `${chestState.trunk_tilt}` : "—"}
            <span className="stat-unit">deg</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isChestReceiving ? "Chest MPU6050 Inclinometer" : "Waiting for Sensor"}
          </div>
        </div>

        {/* 6. AI Movement Repetitions */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Repetition Count</span>
            <span className="badge badge-connected" style={{ fontSize: "0.7rem" }}>
              Random Forest
            </span>
          </div>
          <div className="stat-value" style={{ color: "var(--accent-purple)" }}>
            {isKneeReceiving ? aiLive.rep_count : "—"}
            <span className="stat-unit">reps</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isKneeReceiving ? `${aiLive.exercise_name} Tracking` : "Waiting for Sensor"}
          </div>
        </div>
      </div>

      {/* Main Dual Charts Row */}
      <div className="grid-2">
        {/* ECG Lead II Oscilloscope */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Heart size={18} style={{ color: "var(--accent-rose)" }} />
              Live ECG Biopotential Waveform
            </span>
            <button 
              className="btn btn-secondary" 
              style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
              onClick={() => setActiveTab("chest_belt")}
            >
              Chest Belt View <ArrowUpRight size={13} />
            </button>
          </div>
          <ECGWaveformChart
            ecgBuffer={ecgBuffer}
            isReceiving={isChestReceiving}
            leadsOff={chestState.leads_off}
            heartRate={chestState.heart_rate}
            height={200}
          />
        </div>

        {/* Knee Kinematics Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Activity size={18} style={{ color: "var(--accent-cyan)" }} />
              Live Knee Angle & Flexion Timeline
            </span>
            <button 
              className="btn btn-secondary" 
              style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
              onClick={() => setActiveTab("knee_band")}
            >
              Knee Band View <ArrowUpRight size={13} />
            </button>
          </div>
          <KneeAngleChart
            angleBuffer={kneeAngleBuffer}
            isReceiving={isKneeReceiving}
            currentAngle={kneeState.knee_angle}
            height={200}
          />
        </div>
      </div>

      {/* AI Analysis Snapshot & Plantar Distribution */}
      <div className="grid-2">
        {/* Random Forest AI Snapshot */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Cpu size={18} style={{ color: "var(--accent-cyan)" }} />
              Random Forest Movement Classifier
            </span>
            <span className="badge badge-receiving" style={{ textTransform: "none" }}>
              Scikit-Learn Model
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Detected Movement:</span>
              <strong style={{ fontSize: "1.1rem", color: isKneeReceiving ? "var(--text-primary)" : "var(--text-muted)" }}>
                {isKneeReceiving ? aiLive.exercise_name : "Waiting for Sensor"}
              </strong>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Classification Confidence:</span>
              <span style={{ fontWeight: "700", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                {isKneeReceiving ? `${aiLive.confidence}%` : "—"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Form & Posture Evaluation:</span>
              <span style={{
                color: aiLive.form_score >= 80 ? "var(--accent-emerald)" : (aiLive.form_score >= 60 ? "var(--accent-amber)" : "var(--accent-rose)"),
                fontWeight: "600",
                fontSize: "0.85rem"
              }}>
                {isKneeReceiving ? `${aiLive.form_status} (${aiLive.form_score}/100)` : "Standby"}
              </span>
            </div>

            {aiLive.warnings && aiLive.warnings.length > 0 && isKneeReceiving && (
              <div style={{
                background: "rgba(244, 63, 94, 0.12)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.35rem",
                fontSize: "0.75rem",
                color: "var(--accent-rose)"
              }}>
                <strong>Form Correction Cue:</strong> {aiLive.warnings[0]}
              </div>
            )}

            <button
              className="btn btn-secondary"
              onClick={() => setActiveTab("ai_analysis")}
              style={{ marginTop: "0.5rem" }}
            >
              Open Full AI Pipeline & Analysis <ArrowUpRight size={14} />
            </button>
          </div>
        </div>

        {/* Plantar Load & Joint Bending Snapshot */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Zap size={18} style={{ color: "var(--accent-blue)" }} />
              Plantar Load & Ground Reaction (FSR)
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              FSR Heel & Forefoot
            </span>
          </div>

          <PlantarPressureVisualizer
            heelPressure={kneeState.heel_pressure}
            forefootPressure={kneeState.forefoot_pressure}
            isReceiving={isKneeReceiving}
          />
        </div>
      </div>

      {/* Safety Notice */}
      <MedicalDisclaimer />
    </div>
  );
}
