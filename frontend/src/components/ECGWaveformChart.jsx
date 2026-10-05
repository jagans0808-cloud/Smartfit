import React, { useEffect, useRef } from "react";
import { HeartPulse, AlertTriangle, WifiOff } from "lucide-react";

export default function ECGWaveformChart({ ecgBuffer, isReceiving, leadsOff, heartRate, height = 220 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const h = canvas.height;

    // Clear background
    ctx.fillStyle = "#03170e";
    ctx.fillRect(0, 0, width, h);

    // Draw ECG Medical Grid Lines (10px minor, 50px major)
    ctx.strokeStyle = "rgba(34, 197, 94, 0.08)";
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 20) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Major grid lines
    ctx.strokeStyle = "rgba(34, 197, 94, 0.18)";
    for (let x = 0; x < width; x += 100) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 100) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (!isReceiving || ecgBuffer.length === 0 || leadsOff) {
      return; // Handled by overlay
    }

    // Draw ECG Trace
    ctx.strokeStyle = "#22c55e";
    ctx.lineWidth = 2.2;
    ctx.shadowColor = "#22c55e";
    ctx.shadowBlur = 8;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    ctx.beginPath();
    const len = ecgBuffer.length;
    const step = width / (len - 1 || 1);

    for (let i = 0; i < len; i++) {
      const val = ecgBuffer[i]; // Normalized around 2048 (ADC center)
      // Scale: 2048 is center (h / 2), range +/- 1000 maps to +/- (h * 0.4)
      const normalized = (val - 2048) / 1000.0;
      const y = h / 2 - normalized * (h * 0.42);
      const clampedY = Math.max(10, Math.min(h - 10, y));

      if (i === 0) {
        ctx.moveTo(0, clampedY);
      } else {
        ctx.lineTo(i * step, clampedY);
      }
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

  }, [ecgBuffer, isReceiving, leadsOff]);

  return (
    <div style={{ position: "relative", width: "100%", borderRadius: "0.5rem", overflow: "hidden" }}>
      <canvas
        ref={canvasRef}
        width={700}
        height={height}
        style={{ width: "100%", height: `${height}px`, display: "block" }}
      />

      {/* Header Overlay */}
      <div style={{
        position: "absolute",
        top: "10px",
        left: "14px",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        background: "rgba(3, 23, 14, 0.75)",
        padding: "0.25rem 0.6rem",
        borderRadius: "0.35rem",
        border: "1px solid rgba(34, 197, 94, 0.3)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", color: "#22c55e", fontSize: "0.75rem", fontWeight: "700" }}>
          <HeartPulse size={14} />
          <span>LEAD II (AD8232)</span>
        </div>
        {heartRate && isReceiving && !leadsOff && (
          <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#fff", fontFamily: "var(--font-mono)" }}>
            {heartRate} <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>BPM</span>
          </span>
        )}
      </div>

      {/* Leads-Off Warning Overlay */}
      {leadsOff && isReceiving && (
        <div style={{
          position: "absolute",
          inset: 0,
          background: "rgba(20, 10, 10, 0.85)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--accent-rose)",
          gap: "0.5rem"
        }}>
          <AlertTriangle size={32} />
          <div style={{ fontWeight: "700", fontSize: "0.95rem" }}>ELECTRODE LEADS OFF DETECTED</div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            Check chest electrode contacts (AD8232 LO+ / LO- triggered).
          </div>
        </div>
      )}

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
            Signal Unavailable — Waiting for Sensor
          </div>
          <div style={{ fontSize: "0.75rem" }}>
            Connect Smart Chest Belt (AD8232) or enable Simulator Feed to stream biopotentials.
          </div>
        </div>
      )}
    </div>
  );
}
