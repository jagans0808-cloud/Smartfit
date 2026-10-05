import React from "react";
import { Gauge, ArrowDownUp } from "lucide-react";

export default function PlantarPressureVisualizer({ heelPressure, forefootPressure, isReceiving }) {
  const heelVal = isReceiving && heelPressure !== null ? Math.round(heelPressure) : null;
  const forefootVal = isReceiving && forefootPressure !== null ? Math.round(forefootPressure) : null;

  const total = (heelVal || 0) + (forefootVal || 0) || 1;
  const heelPct = heelVal !== null ? Math.round(((heelVal) / total) * 100) : 50;
  const forefootPct = forefootVal !== null ? Math.round(((forefootVal) / total) * 100) : 50;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)" }}>
          Plantar Load Distribution (FSR)
        </span>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          {isReceiving ? "FSR Dual-Zone" : "No Data"}
        </span>
      </div>

      {/* Visual Bar Distribution */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.3rem" }}>
          <span style={{ color: "var(--accent-blue)" }}>Heel: {heelVal !== null ? `${heelVal}% (${heelPct}%)` : "—"}</span>
          <span style={{ color: "var(--accent-cyan)" }}>Forefoot: {forefootVal !== null ? `${forefootVal}% (${forefootPct}%)` : "—"}</span>
        </div>
        <div style={{
          height: "10px",
          borderRadius: "5px",
          background: "var(--bg-primary)",
          overflow: "hidden",
          display: "flex",
          border: "1px solid var(--border-color)"
        }}>
          <div style={{
            width: isReceiving ? `${heelPct}%` : "50%",
            background: "linear-gradient(90deg, #2563eb, #3b82f6)",
            transition: "width 0.2s ease"
          }}></div>
          <div style={{
            width: isReceiving ? `${forefootPct}%` : "50%",
            background: "linear-gradient(90deg, #06b6d4, #14b8a6)",
            transition: "width 0.2s ease"
          }}></div>
        </div>
      </div>

      {/* Foot Graphic Visualizer */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "1.5rem",
        padding: "0.75rem",
        background: "var(--bg-primary)",
        borderRadius: "0.5rem",
        border: "1px solid var(--border-color)"
      }}>
        {/* Anatomical Insole Outline */}
        <div style={{ position: "relative", width: "70px", height: "130px" }}>
          <svg viewBox="0 0 100 200" style={{ width: "100%", height: "100%" }}>
            {/* Foot sole path */}
            <path
              d="M 50 10 C 75 10, 85 40, 80 80 C 75 120, 70 140, 75 170 C 75 190, 60 195, 50 195 C 40 195, 25 190, 25 170 C 30 140, 25 120, 20 80 C 15 40, 25 10, 50 10 Z"
              fill="var(--bg-elevated)"
              stroke="var(--border-light)"
              strokeWidth="2"
            />

            {/* Forefoot FSR Zone */}
            <circle
              cx="50"
              cy="55"
              r="22"
              fill={isReceiving && forefootVal > 10 ? `rgba(6, 182, 212, ${Math.min(0.9, 0.2 + (forefootVal / 100))})` : "rgba(100, 116, 139, 0.2)"}
              stroke="var(--accent-cyan)"
              strokeWidth="1.5"
            />
            <text x="50" y="58" fontSize="11" fill="#fff" textAnchor="middle" fontWeight="bold">
              {forefootVal !== null ? `${forefootVal}%` : "FSR"}
            </text>

            {/* Heel FSR Zone */}
            <circle
              cx="50"
              cy="165"
              r="20"
              fill={isReceiving && heelVal > 10 ? `rgba(37, 99, 235, ${Math.min(0.9, 0.2 + (heelVal / 100))})` : "rgba(100, 116, 139, 0.2)"}
              stroke="var(--accent-blue)"
              strokeWidth="1.5"
            />
            <text x="50" y="168" fontSize="11" fill="#fff" textAnchor="middle" fontWeight="bold">
              {heelVal !== null ? `${heelVal}%` : "FSR"}
            </text>
          </svg>
        </div>

        {/* Load Status Summary */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.8rem" }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Heel Pressure:</span>{" "}
            <strong>{heelVal !== null ? `${heelVal} %` : "No Data"}</strong>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Forefoot Pressure:</span>{" "}
            <strong>{forefootVal !== null ? `${forefootVal} %` : "No Data"}</strong>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Gait Stance:</span>{" "}
            <span style={{ color: isReceiving ? "var(--accent-emerald)" : "var(--text-muted)" }}>
              {isReceiving 
                ? (heelVal > forefootVal + 15 ? "Heel Loading (Contact)" : (forefootVal > heelVal + 15 ? "Forefoot Loading (Push-Off)" : "Balanced Stance"))
                : "Sensor Standby"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
