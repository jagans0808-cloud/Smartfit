import React from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "../components/SensorStatusBadge";
import MedicalDisclaimer from "../components/MedicalDisclaimer";
import { 
  Radio, Cpu, Wifi, Battery, Layers, CheckCircle2, 
  AlertCircle, Vibrate, RefreshCw, Terminal
} from "lucide-react";

export default function DeviceHardware() {
  const { kneeState, chestState, simulationMode, toggleSimulation, triggerVibration } = useSmartFit();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>Device Hardware & Communication Setup</h2>
          <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
            Physical hardware pinouts, ESP-NOW wireless peer-to-peer link, and WebSocket protocol (Biomedfinix2).
          </p>
        </div>

        <button
          className="btn btn-secondary"
          onClick={() => toggleSimulation(!simulationMode)}
        >
          {simulationMode ? "Switch to Physical Sensor Waiting" : "Activate Test Telemetry Feed"}
        </button>
      </div>

      {/* Communication Protocol Flow Card */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <Radio size={18} style={{ color: "var(--accent-cyan)" }} />
            Communication Architecture (Biomedfinix2 Workflow)
          </span>
          <span className="badge badge-connected">Cable-Free Local Link</span>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1rem",
          background: "var(--bg-primary)",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-color)",
          fontSize: "0.85rem"
        }}>
          <div>
            <div style={{ color: "var(--accent-cyan)", fontWeight: "700", marginBottom: "0.25rem" }}>
              1. Smart Knee Band (ESP32)
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
              Samples MPU6050s, Flex Sensor, and FSRs. Bundles structured telemetry packet and broadcasts over <strong>ESP-NOW</strong> peer-to-peer.
            </div>
          </div>

          <div>
            <div style={{ color: "var(--accent-rose)", fontWeight: "700", marginBottom: "0.25rem" }}>
              2. Smart Chest Belt (ESP32 Gateway)
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
              Samples AD8232 ECG, MAX30102 & MPU6050. Receives Knee Band ESP-NOW packets and fuses them into a synchronized telemetry stream.
            </div>
          </div>

          <div>
            <div style={{ color: "var(--accent-emerald)", fontWeight: "700", marginBottom: "0.25rem" }}>
              3. WebSocket Stream to Web App
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
              Streams time-aligned JSON payloads over local WebSocket to the SmartFit React interface. <strong>No Internet required</strong>.
            </div>
          </div>
        </div>
      </div>

      {/* Dual Hardware Pinout Reference Tables (Strictly PPT) */}
      <div className="grid-2">
        {/* Knee Band Hardware */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Cpu size={18} style={{ color: "var(--accent-cyan)" }} />
              Smart Knee Band Hardware (Only PPT Specified)
            </span>
            <SensorStatusBadge status={kneeState.status} />
          </div>

          <table style={{ width: "100%", fontSize: "0.8rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.4rem" }}>Component</th>
                <th style={{ padding: "0.4rem" }}>GPIO / Pin</th>
                <th style={{ padding: "0.4rem" }}>Interface</th>
                <th style={{ padding: "0.4rem" }}>Role</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>ESP32 Node</td>
                <td style={{ padding: "0.4rem" }}>—</td>
                <td style={{ padding: "0.4rem" }}>ESP-NOW</td>
                <td style={{ padding: "0.4rem" }}>Controller</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>MPU6050 (Thigh)</td>
                <td style={{ padding: "0.4rem" }}>SDA 21, SCL 22</td>
                <td style={{ padding: "0.4rem" }}>I2C 0x68</td>
                <td style={{ padding: "0.4rem" }}>Thigh motion</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>MPU6050 (Shin)</td>
                <td style={{ padding: "0.4rem" }}>SDA 21, SCL 22</td>
                <td style={{ padding: "0.4rem" }}>I2C 0x69</td>
                <td style={{ padding: "0.4rem" }}>Shin motion</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>Flex Sensor</td>
                <td style={{ padding: "0.4rem" }}>GPIO 36</td>
                <td style={{ padding: "0.4rem" }}>ADC1_CH0</td>
                <td style={{ padding: "0.4rem" }}>Joint curvature</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>FSR (Heel)</td>
                <td style={{ padding: "0.4rem" }}>GPIO 39</td>
                <td style={{ padding: "0.4rem" }}>ADC1_CH3</td>
                <td style={{ padding: "0.4rem" }}>Heel pressure</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>FSR (Forefoot)</td>
                <td style={{ padding: "0.4rem" }}>GPIO 34</td>
                <td style={{ padding: "0.4rem" }}>ADC1_CH6</td>
                <td style={{ padding: "0.4rem" }}>Forefoot pressure</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>Vibration Motor</td>
                <td style={{ padding: "0.4rem" }}>GPIO 26</td>
                <td style={{ padding: "0.4rem" }}>Digital OUT</td>
                <td style={{ padding: "0.4rem" }}>Haptic form cue</td>
              </tr>
              <tr>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>Li-ion Battery</td>
                <td style={{ padding: "0.4rem" }}>3.7V / BAT</td>
                <td style={{ padding: "0.4rem" }}>Power</td>
                <td style={{ padding: "0.4rem" }}>Wireless supply</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Chest Belt Hardware */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Cpu size={18} style={{ color: "var(--accent-rose)" }} />
              Smart Chest Belt Hardware (Only PPT Specified)
            </span>
            <SensorStatusBadge status={chestState.status} />
          </div>

          <table style={{ width: "100%", fontSize: "0.8rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.4rem" }}>Component</th>
                <th style={{ padding: "0.4rem" }}>GPIO / Pin</th>
                <th style={{ padding: "0.4rem" }}>Interface</th>
                <th style={{ padding: "0.4rem" }}>Role</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>ESP32 Gateway</td>
                <td style={{ padding: "0.4rem" }}>—</td>
                <td style={{ padding: "0.4rem" }}>Wi-Fi / WS</td>
                <td style={{ padding: "0.4rem" }}>Hub & Aggregator</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>AD8232 ECG OUT</td>
                <td style={{ padding: "0.4rem" }}>GPIO 34</td>
                <td style={{ padding: "0.4rem" }}>ADC1_CH6</td>
                <td style={{ padding: "0.4rem" }}>Lead-II Biopotential</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>AD8232 LO+ / LO-</td>
                <td style={{ padding: "0.4rem" }}>GPIO 32, 33</td>
                <td style={{ padding: "0.4rem" }}>Digital IN</td>
                <td style={{ padding: "0.4rem" }}>Leads-Off Detection</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>MAX30102 PPG</td>
                <td style={{ padding: "0.4rem" }}>SDA 21, SCL 22</td>
                <td style={{ padding: "0.4rem" }}>I2C 0x57</td>
                <td style={{ padding: "0.4rem" }}>SpO2 & Heart Rate</td>
              </tr>
              <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>MPU6050 (Chest)</td>
                <td style={{ padding: "0.4rem" }}>SDA 21, SCL 22</td>
                <td style={{ padding: "0.4rem" }}>I2C 0x68</td>
                <td style={{ padding: "0.4rem" }}>Thoracic tilt / IMU</td>
              </tr>
              <tr>
                <td style={{ padding: "0.4rem", fontWeight: "600" }}>Li-ion Battery</td>
                <td style={{ padding: "0.4rem" }}>3.7V / BAT</td>
                <td style={{ padding: "0.4rem" }}>Power</td>
                <td style={{ padding: "0.4rem" }}>Wireless supply</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Real-Time Telemetry Packet Inspector */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <Terminal size={18} style={{ color: "var(--accent-emerald)" }} />
            Live Telemetry JSON Packet Inspector
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            WebSocket: ws://localhost:8000/ws/live
          </span>
        </div>

        <pre style={{
          background: "var(--bg-primary)",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-color)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.75rem",
          color: "var(--accent-cyan)",
          overflowX: "auto",
          maxHeight: "180px"
        }}>
          {JSON.stringify({
            timestamp: Date.now(),
            knee_band: {
              status: kneeState.status,
              connected: kneeState.connected,
              battery: kneeState.battery,
              knee_angle: kneeState.knee_angle,
              flex_sensor: kneeState.flex_sensor,
              heel_pressure: kneeState.heel_pressure,
              forefoot_pressure: kneeState.forefoot_pressure,
              vibration_motor: kneeState.vibration_motor
            },
            chest_belt: {
              status: chestState.status,
              connected: chestState.connected,
              battery: chestState.battery,
              ecg_raw: chestState.ecg_raw,
              heart_rate: chestState.heart_rate,
              spo2: chestState.spo2,
              trunk_tilt: chestState.trunk_tilt,
              leads_off: chestState.leads_off
            }
          }, null, 2)}
        </pre>
      </div>

      <MedicalDisclaimer />
    </div>
  );
}
