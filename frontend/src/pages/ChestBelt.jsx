import React from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "../components/SensorStatusBadge";
import ECGWaveformChart from "../components/ECGWaveformChart";
import MedicalDisclaimer from "../components/MedicalDisclaimer";
import { 
  Heart, HeartPulse, Battery, Activity, 
  AlertTriangle, ShieldCheck, Compass, Zap
} from "lucide-react";

export default function ChestBelt() {
  const { chestState, ecgBuffer } = useSmartFit();

  const isReceiving = chestState.status === "RECEIVING_DATA";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>Smart Chest Belt</h2>
            <SensorStatusBadge status={chestState.status} />
            {chestState.connected && (
              <span style={{ fontSize: "0.8rem", color: "var(--accent-emerald)", display: "flex", alignItems: "center", gap: "3px" }}>
                <Battery size={14} /> {chestState.battery}%
              </span>
            )}
          </div>
          <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
            Cardiovascular biopotentials, optical photoplethysmography, and thoracic kinetic monitoring.
          </p>
        </div>

        {/* Leads-Off Status Alert */}
        {chestState.leads_off && isReceiving && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.35rem 0.75rem",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "0.4rem",
            color: "var(--accent-rose)",
            fontSize: "0.8rem",
            fontWeight: "600"
          }}>
            <AlertTriangle size={15} />
            <span>Leads-Off Active (Check Skin Contact)</span>
          </div>
        )}
      </div>

      {/* Hardware Component Diagnostic Strip (Strictly PPT) */}
      <div className="card" style={{ padding: "0.85rem 1.25rem" }}>
        <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
          Hardware & Sensor Nodes (Biomedfinix2 Architecture)
        </div>
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", fontSize: "0.8rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span className="pulse-dot green"></span>
            <strong>ESP32:</strong> Gateway Hub (ESP-NOW + WebSocket)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span className="pulse-dot rose"></span>
            <strong>AD8232:</strong> Single-Lead Biopotential ECG (GPIO 34, LO+ 32, LO- 33)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span className="pulse-dot emerald"></span>
            <strong>MAX30102:</strong> Optical PPG / SpO2 / Pulse (I2C 0x57)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span className="pulse-dot cyan"></span>
            <strong>MPU6050:</strong> Thoracic Motion & Posture IMU (I2C 0x68)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span className="pulse-dot blue"></span>
            <strong>Power:</strong> 3.7V Rechargeable Li-ion Battery
          </div>
        </div>
      </div>

      {/* Large ECG Lead II Oscilloscope Chart */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <HeartPulse size={18} style={{ color: "var(--accent-rose)" }} />
            High-Speed Lead II Electrocardiogram (AD8232)
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            <span>Bandpass Filter: 0.5 – 40 Hz</span>
            <span>Sampling: ~50 Hz Telemetry</span>
          </div>
        </div>

        <ECGWaveformChart
          ecgBuffer={ecgBuffer}
          isReceiving={isReceiving}
          leadsOff={chestState.leads_off}
          heartRate={chestState.heart_rate}
          height={260}
        />
      </div>

      {/* Physiological Parameters & Trunk Posture Grid */}
      <div className="grid-3">
        {/* Heart Rate */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Heart Rate</span>
            <span className="badge badge-connected" style={{ fontSize: "0.7rem" }}>AD8232 / MAX30102</span>
          </div>
          <div className="stat-value" style={{ color: "var(--accent-rose)" }}>
            {isReceiving && chestState.heart_rate !== null ? `${chestState.heart_rate}` : "—"}
            <span className="stat-unit">BPM</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isReceiving 
              ? (chestState.heart_rate < 60 ? "Bradycardia Range" : (chestState.heart_rate > 100 ? "Tachycardia / Exertion" : "Normative Resting"))
              : "Waiting for Sensor"}
          </div>
        </div>

        {/* SpO2 */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Blood Oxygen (SpO2)</span>
            <span className="badge badge-connected" style={{ fontSize: "0.7rem" }}>MAX30102</span>
          </div>
          <div className="stat-value" style={{ color: "var(--accent-emerald)" }}>
            {isReceiving && chestState.spo2 !== null ? `${chestState.spo2}` : "—"}
            <span className="stat-unit">%</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isReceiving ? (chestState.spo2 >= 95 ? "Normal Oxygenation" : "Low Saturation Warning") : "Waiting for Sensor"}
          </div>
        </div>

        {/* Trunk Incline Tilt */}
        <div className="stat-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="stat-label">Trunk Posture Inclination</span>
            <span className="badge badge-connected" style={{ fontSize: "0.7rem" }}>MPU6050</span>
          </div>
          <div className="stat-value" style={{ color: "var(--accent-amber)" }}>
            {isReceiving && chestState.trunk_tilt !== null ? `${chestState.trunk_tilt}` : "—"}
            <span className="stat-unit">deg</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {isReceiving ? (chestState.trunk_tilt < 15 ? "Upright Posture" : "Forward Trunk Flexion") : "Waiting for Sensor"}
          </div>
        </div>
      </div>

      {/* Tri-Axial Thoracic Motion (MPU6050) */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <Compass size={18} style={{ color: "var(--accent-cyan)" }} />
            Thoracic Tri-Axial Kinetic Motion (MPU6050)
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Units: m/s²
          </span>
        </div>

        <div className="grid-3" style={{ textAlign: "center" }}>
          <div className="stat-box">
            <span className="stat-label">Lateral (X-Axis)</span>
            <div className="stat-value" style={{ fontSize: "1.2rem" }}>
              {isReceiving && chestState.accel_x !== null ? `${chestState.accel_x}` : "—"}
              <span className="stat-unit">m/s²</span>
            </div>
          </div>

          <div className="stat-box">
            <span className="stat-label">Anteroposterior (Y-Axis)</span>
            <div className="stat-value" style={{ fontSize: "1.2rem" }}>
              {isReceiving && chestState.accel_y !== null ? `${chestState.accel_y}` : "—"}
              <span className="stat-unit">m/s²</span>
            </div>
          </div>

          <div className="stat-box">
            <span className="stat-label">Vertical Gravity (Z-Axis)</span>
            <div className="stat-value" style={{ fontSize: "1.2rem" }}>
              {isReceiving && chestState.accel_z !== null ? `${chestState.accel_z}` : "—"}
              <span className="stat-unit">m/s²</span>
            </div>
          </div>
        </div>
      </div>

      <MedicalDisclaimer />
    </div>
  );
}
