import React from "react";
import { Compass, RotateCw } from "lucide-react";

export default function JointFlexionGauge({ flexSensor, isReceiving }) {
  const flexVal = isReceiving && flexSensor !== null ? Math.round(flexSensor) : null;
  const pct = flexVal !== null ? Math.min(100, Math.max(0, (flexVal / 90) * 100)) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)" }}>
          Flex Sensor Curvature (ADC Fusion)
        </span>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          {isReceiving ? `${flexVal}° Curvature` : "No Data"}
        </span>
      </div>

      {/* Progress Arc / Bar */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div style={{ position: "relative", width: "70px", height: "70px", flexShrink: 0 }}>
          <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", transform: "rotate(-90deg)" }}>
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="transparent"
              stroke="var(--bg-elevated)"
              strokeWidth="10"
            />
            {isReceiving && flexVal !== null && (
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                stroke="var(--accent-purple)"
                strokeWidth="10"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - pct / 100)}`}
                strokeLinecap="round"
                style={{ transition: "stroke-dashoffset 0.2s ease" }}
              />
            )}
          </svg>
          <div style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.95rem",
            fontWeight: "700",
            fontFamily: "var(--font-mono)",
            color: isReceiving ? "var(--text-primary)" : "var(--text-muted)"
          }}>
            {flexVal !== null ? `${flexVal}°` : "—"}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.8rem" }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Joint Curvature:</span>{" "}
            <strong>{flexVal !== null ? `${flexVal} degrees` : "Waiting for Sensor"}</strong>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Flex State:</span>{" "}
            <span style={{ color: isReceiving ? "var(--accent-purple)" : "var(--text-muted)" }}>
              {isReceiving 
                ? (flexVal < 25 ? "Extension (Straight)" : (flexVal < 60 ? "Moderate Flexion" : "Deep Flexion"))
                : "Signal Unavailable"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
