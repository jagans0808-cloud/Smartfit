import React from "react";
import { Activity, WifiOff } from "lucide-react";

export default function KneeAngleChart({ angleBuffer, isReceiving, currentAngle, height = 220 }) {
  const width = 600;
  const padding = { top: 20, right: 20, bottom: 25, left: 45 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Knee angle scale: 40 deg (bottom) to 180 deg (top)
  const minAngle = 40;
  const maxAngle = 180;

  const getY = (val) => {
    const clamped = Math.max(minAngle, Math.min(maxAngle, val));
    const ratio = (clamped - minAngle) / (maxAngle - minAngle);
    return padding.top + graphHeight * (1 - ratio);
  };

  const points = angleBuffer.map((val, idx) => {
    const x = padding.left + (idx / Math.max(angleBuffer.length - 1, 1)) * graphWidth;
    const y = getY(val);
    return `${x},${y}`;
  }).join(" ");

  return (
    <div style={{ position: "relative", width: "100%", background: "var(--bg-elevated)", borderRadius: "0.5rem", overflow: "hidden" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: `${height}px`, display: "block" }}
      >
        {/* Horizontal Guide Lines */}
        {[60, 90, 120, 160].map(deg => {
          const y = getY(deg);
          return (
            <g key={deg}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="var(--chart-grid)"
                strokeDasharray="4,4"
              />
              <text
                x={padding.left - 8}
                y={y + 4}
                fill="var(--text-muted)"
                fontSize="10"
                textAnchor="end"
                fontFamily="var(--font-mono)"
              >
                {deg}°
              </text>
            </g>
          );
        })}

        {/* 90° Parallel Flexion Threshold Highlight */}
        <line
          x1={padding.left}
          y1={getY(90)}
          x2={width - padding.right}
          y2={getY(90)}
          stroke="rgba(2, 132, 199, 0.4)"
          strokeWidth="1.5"
          strokeDasharray="6,4"
        />

        {/* Plot Data Path */}
        {isReceiving && angleBuffer.length > 1 && (
          <>
            <polyline
              fill="none"
              stroke="var(--accent-cyan)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={points}
            />
            {/* Pulsing Dot at current head point */}
            <circle
              cx={padding.left + graphWidth}
              cy={getY(currentAngle || angleBuffer[angleBuffer.length - 1])}
              r="4.5"
              fill="var(--bg-card)"
              stroke="var(--accent-cyan)"
              strokeWidth="2.5"
            />
          </>
        )}
      </svg>

      {/* Header Overlay */}
      <div style={{
        position: "absolute",
        top: "10px",
        left: "14px",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        background: "var(--bg-card)",
        padding: "0.25rem 0.6rem",
        borderRadius: "0.35rem",
        border: "1px solid var(--border-color)",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", color: "var(--accent-cyan)", fontSize: "0.75rem", fontWeight: "700" }}>
          <Activity size={14} />
          <span>KNEE JOINT KINEMATICS</span>
        </div>
        {currentAngle !== null && isReceiving && (
          <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
            {currentAngle}° <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>ANGLE</span>
          </span>
        )}
      </div>

      {/* Disconnected / Waiting Overlay */}
      {!isReceiving && (
        <div style={{
          position: "absolute",
          inset: 0,
          background: "var(--bg-elevated)",
          opacity: 0.95,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-muted)",
          gap: "0.5rem"
        }}>
          <WifiOff size={28} />
          <div style={{ fontWeight: "600", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
            No Data — Waiting for Sensor
          </div>
          <div style={{ fontSize: "0.75rem" }}>
            Connect Smart Knee Band (MPU6050 + Flex Sensor) to visualize joint angle.
          </div>
        </div>
      )}
    </div>
  );
}
