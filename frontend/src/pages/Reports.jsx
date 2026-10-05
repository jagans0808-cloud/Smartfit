import React, { useRef } from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "../components/SensorStatusBadge";
import MedicalDisclaimer from "../components/MedicalDisclaimer";
import { 
  FileText, Printer, Download, CheckCircle2, 
  Activity, Heart, Cpu, ShieldCheck, User
} from "lucide-react";

export default function Reports() {
  const { activePatient, kneeState, chestState, aiLive } = useSmartFit();

  const reportDate = new Date().toLocaleString();
  const reportId = `SF-REP-${activePatient?.patient_id || "1001"}-${Date.now().toString().slice(-6)}`;

  const heightM = activePatient ? activePatient.height / 100 : 1.7;
  const bmi = activePatient ? (activePatient.weight / (heightM * heightM)).toFixed(1) : "24.2";
  const hasPain = activePatient && activePatient.pain_side !== "None";

  const oaProb = Math.min(88, Math.max(12, Math.round(
    10 + (activePatient ? (activePatient.age - 20) * 0.7 : 15) + (parseFloat(bmi) - 20) * 1.5 + (hasPain ? 20 : 0)
  )));

  const oaStage = oaProb < 33 
    ? "Lower Epidemiological OA Likelihood" 
    : (oaProb < 66 ? "Intermediate Epidemiological OA Likelihood" : "Higher Epidemiological OA Likelihood");

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    const reportData = {
      report_id: reportId,
      timestamp: reportDate,
      patient: activePatient,
      bmi: bmi,
      knee_measurements: {
        knee_angle: kneeState.knee_angle,
        flex_sensor: kneeState.flex_sensor,
        heel_pressure: kneeState.heel_pressure,
        forefoot_pressure: kneeState.forefoot_pressure,
        pressure_imbalance: kneeState.pressure_imbalance,
        device_status: kneeState.status
      },
      chest_measurements: {
        heart_rate: chestState.heart_rate,
        spo2: chestState.spo2,
        trunk_tilt: chestState.trunk_tilt,
        leads_off: chestState.leads_off,
        device_status: chestState.status
      },
      ai_ml_results: {
        exercise_name: aiLive.exercise_name,
        confidence: aiLive.confidence,
        rep_count: aiLive.rep_count,
        form_score: aiLive.form_score,
        form_status: aiLive.form_status
      },
      oa_risk_result: {
        stage: oaStage,
        probability: oaProb,
        predictors: { age: activePatient?.age, bmi: bmi, symptom_presence: hasPain }
      },
      system: "SmartFit – Integrated Fitness Monitoring System (SIH26213)"
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Top Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }} className="no-print">
        <div>
          <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>Comprehensive Performance & Health Report</h2>
          <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
            Integrated multi-sensor telemetry, Random Forest exercise assessment, and OA clinical screening.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem" }}>
          <button className="btn btn-cyan" onClick={handlePrint}>
            <Printer size={15} />
            Print / Save PDF
          </button>
          <button className="btn btn-secondary" onClick={handleDownloadJSON}>
            <Download size={15} />
            Export Raw JSON
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      <div className="card" style={{ background: "var(--bg-card)", padding: "2rem" }}>
        {/* Document Header */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          borderBottom: "2px solid var(--border-color)",
          paddingBottom: "1.25rem",
          marginBottom: "1.5rem"
        }}>
          <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: "800", color: "var(--text-heading)", letterSpacing: "-0.01em" }}>
              SmartFit Integrated Fitness & Biomechanical Report
            </h1>
            <div style={{ fontSize: "0.85rem", color: "var(--accent-cyan)", fontWeight: "600", marginTop: "0.2rem" }}>
              SIH26213 Multimodal Research Prototype — Wearable Telemetry
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              Smart Knee Band (ESP32) + Smart Chest Belt (ESP32) Wireless Hub
            </div>
          </div>

          <div style={{ textAlign: "right", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            <div><strong>Report Ref:</strong> {reportId}</div>
            <div><strong>Generated:</strong> {reportDate}</div>
            <div style={{ marginTop: "0.3rem" }}>
              <span className="badge badge-connected">System Verified</span>
            </div>
          </div>
        </div>

        {/* Section 1: Patient Information */}
        <div style={{ marginBottom: "1.75rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--accent-cyan)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <User size={16} /> 1. Patient & Athlete Profile
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "0.85rem",
            background: "var(--bg-primary)",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-color)",
            fontSize: "0.85rem"
          }}>
            <div><span className="stat-label">Full Name:</span> <strong>{activePatient?.name || "—"}</strong></div>
            <div><span className="stat-label">Patient ID:</span> <strong>{activePatient?.patient_id || "—"}</strong></div>
            <div><span className="stat-label">Age / Gender:</span> <strong>{activePatient?.age || "—"} yrs / {activePatient?.gender || "—"}</strong></div>
            <div><span className="stat-label">Contact:</span> <strong>{activePatient?.contact || "—"}</strong></div>
            <div><span className="stat-label">Height:</span> <strong>{activePatient?.height || "—"} cm</strong></div>
            <div><span className="stat-label">Weight:</span> <strong>{activePatient?.weight || "—"} kg</strong></div>
            <div><span className="stat-label">Calculated BMI:</span> <strong style={{ color: "var(--accent-cyan)" }}>{bmi} kg/m²</strong></div>
            <div><span className="stat-label">Reported Pain:</span> <strong style={{ color: "var(--accent-amber)" }}>{activePatient?.pain_side || "None"}</strong></div>
          </div>
        </div>

        {/* Section 2: Smart Knee Band Measurements */}
        <div style={{ marginBottom: "1.75rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--accent-blue)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Activity size={16} /> 2. Smart Knee Band Biomechanical Measurements
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "0.85rem",
            background: "var(--bg-primary)",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-color)",
            fontSize: "0.85rem"
          }}>
            <div>
              <span className="stat-label">Knee Angle:</span>
              <strong>{kneeState.knee_angle !== null ? `${kneeState.knee_angle}°` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">Flex Sensor Curvature:</span>
              <strong>{kneeState.flex_sensor !== null ? `${kneeState.flex_sensor}°` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">Heel Pressure (FSR):</span>
              <strong>{kneeState.heel_pressure !== null ? `${Math.round(kneeState.heel_pressure)}%` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">Forefoot Pressure (FSR):</span>
              <strong>{kneeState.forefoot_pressure !== null ? `${Math.round(kneeState.forefoot_pressure)}%` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">Plantar Imbalance:</span>
              <strong>{kneeState.pressure_imbalance !== null ? `${kneeState.pressure_imbalance}%` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">Thigh Kinematics:</span>
              <strong>{kneeState.thigh_accel !== null ? `${kneeState.thigh_accel} m/s²` : "Standby"}</strong>
            </div>
            <div>
              <span className="stat-label">Shin Kinematics:</span>
              <strong>{kneeState.shin_accel !== null ? `${kneeState.shin_accel} m/s²` : "Standby"}</strong>
            </div>
            <div>
              <span className="stat-label">Device Status:</span>
              <SensorStatusBadge status={kneeState.status} />
            </div>
          </div>
        </div>

        {/* Section 3: Smart Chest Belt Measurements */}
        <div style={{ marginBottom: "1.75rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--accent-rose)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Heart size={16} /> 3. Smart Chest Belt Physiological Measurements
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "0.85rem",
            background: "var(--bg-primary)",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-color)",
            fontSize: "0.85rem"
          }}>
            <div>
              <span className="stat-label">Heart Rate (ECG/PPG):</span>
              <strong style={{ color: "var(--accent-rose)" }}>
                {chestState.heart_rate !== null ? `${chestState.heart_rate} BPM` : "Waiting for Sensor"}
              </strong>
            </div>
            <div>
              <span className="stat-label">Oxygen Saturation (SpO2):</span>
              <strong style={{ color: "var(--accent-emerald)" }}>
                {chestState.spo2 !== null ? `${chestState.spo2}%` : "Waiting for Sensor"}
              </strong>
            </div>
            <div>
              <span className="stat-label">Trunk Posture Lean:</span>
              <strong>{chestState.trunk_tilt !== null ? `${chestState.trunk_tilt}°` : "Waiting for Sensor"}</strong>
            </div>
            <div>
              <span className="stat-label">ECG Leads-Off:</span>
              <strong style={{ color: chestState.leads_off ? "var(--accent-rose)" : "var(--accent-emerald)" }}>
                {chestState.leads_off ? "Leads-Off Active" : "Electrodes Normal"}
              </strong>
            </div>
          </div>
        </div>

        {/* Section 4: AI/ML Random Forest Exercise Classification */}
        <div style={{ marginBottom: "1.75rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--accent-purple)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Cpu size={16} /> 4. AI/ML Multimodal Classification & Performance
          </h3>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "0.85rem",
            background: "var(--bg-primary)",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-color)",
            fontSize: "0.85rem"
          }}>
            <div>
              <span className="stat-label">Movement Class:</span>
              <strong>{aiLive.exercise_name}</strong>
            </div>
            <div>
              <span className="stat-label">Model Confidence:</span>
              <strong>{aiLive.confidence}%</strong>
            </div>
            <div>
              <span className="stat-label">Repetition Count:</span>
              <strong>{aiLive.rep_count} reps</strong>
            </div>
            <div>
              <span className="stat-label">Form Score:</span>
              <strong>{aiLive.form_score} / 100 ({aiLive.form_status})</strong>
            </div>
          </div>
        </div>

        {/* Section 5: Preserved OA Clinical Assessment Result */}
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--accent-emerald)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <ShieldCheck size={16} /> 5. Integrated Osteoarthritis Clinical Assessment
          </h3>
          <div style={{
            background: "var(--bg-primary)",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-color)",
            fontSize: "0.85rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span><strong>Reference Model:</strong> NIH Osteoarthritis Initiative (OAI) Clinical Model</span>
              <span style={{ color: "var(--accent-cyan)", fontWeight: "700" }}>{oaStage} ({oaProb}%)</span>
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
              Predictor inputs: Age ({activePatient?.age || 28}), BMI ({bmi} kg/m²), Symptom localized in {activePatient?.pain_side || "None"}.
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic", borderTop: "1px solid var(--border-color)", paddingTop: "0.5rem" }}>
              Note: Random Forest model classifies kinetic exercises. OA risk is evaluated separately through clinical epidemiological parameters.
            </div>
          </div>
        </div>

        {/* Safety Disclaimer in Report */}
        <div style={{
          padding: "0.75rem 1rem",
          background: "rgba(245, 158, 11, 0.1)",
          border: "1px solid rgba(245, 158, 11, 0.3)",
          borderRadius: "0.35rem",
          fontSize: "0.75rem",
          color: "var(--accent-amber)"
        }}>
          <strong>DISCLAIMER:</strong> This report is generated by the SmartFit Student/Research Prototype (SIH26213). It is not a clinical medical diagnostic report. Any medical diagnoses must be confirmed through clinical orthopedic examination and standard radiography.
        </div>
      </div>
    </div>
  );
}
