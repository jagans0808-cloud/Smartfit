import React, { useState, useEffect } from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "./SensorStatusBadge";
import { 
  Activity, Heart, Battery, UserCheck, 
  Wifi, SlidersHorizontal, Sun, Moon
} from "lucide-react";

export default function Header() {
  const { 
    activePatient, patients, setActivePatient, 
    kneeState, chestState, backendOnline,
    simulationMode, toggleSimulation
  } = useSmartFit();

  const [theme, setTheme] = useState(() => localStorage.getItem("smartfit_theme") || "light");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("smartfit_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === "light" ? "dark" : "light");
  };

  return (
    <header style={{
      background: "var(--bg-secondary)",
      borderBottom: "1px solid var(--border-color)",
      padding: "0.85rem 1.5rem",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      flexWrap: "wrap",
      gap: "1rem"
    }} className="top-header">
      {/* Title & Branding */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
        <div style={{
          width: "36px",
          height: "36px",
          borderRadius: "8px",
          background: "linear-gradient(135deg, #0284c7, #2563eb)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          boxShadow: "0 2px 8px rgba(2, 132, 199, 0.3)"
        }}>
          <Activity size={22} />
        </div>
        <div>
          <h1 style={{ fontSize: "1.15rem", fontWeight: "700", letterSpacing: "-0.01em", color: "var(--text-heading)" }}>
            SmartFit
          </h1>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "500" }}>
            Integrated Fitness Monitoring System
          </p>
        </div>
      </div>

      {/* Middle: Active Patient Selector */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "0.6rem",
        background: "var(--bg-card)",
        padding: "0.35rem 0.85rem",
        borderRadius: "0.5rem",
        border: "1px solid var(--border-color)",
        boxShadow: "0 1px 2px rgba(0,0,0,0.05)"
      }}>
        <UserCheck size={16} style={{ color: "var(--accent-cyan)" }} />
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Active Patient:</span>
        <select
          value={activePatient ? activePatient.patient_id : ""}
          onChange={(e) => {
            const p = patients.find(item => item.patient_id === e.target.value);
            if (p) setActivePatient(p);
          }}
          style={{
            background: "transparent",
            color: "var(--text-primary)",
            border: "none",
            fontSize: "0.85rem",
            fontWeight: "600",
            cursor: "pointer",
            outline: "none"
          }}
        >
          {patients.map(p => (
            <option key={p.patient_id} value={p.patient_id} style={{ background: "var(--bg-card)", color: "var(--text-primary)" }}>
              {p.name} ({p.patient_id})
            </option>
          ))}
        </select>
        {activePatient && (
          <span style={{ fontSize: "0.75rem", color: "var(--accent-blue)", fontWeight: "600", paddingLeft: "4px" }}>
            BMI: {(activePatient.weight / ((activePatient.height / 100) ** 2)).toFixed(1)}
          </span>
        )}
      </div>

      {/* Right: Device Status & Mode Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {/* Knee Band Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <Activity size={15} style={{ color: "var(--accent-cyan)" }} />
          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "500" }}>Knee:</span>
          <SensorStatusBadge status={kneeState.status} />
          {kneeState.connected && (
            <span style={{ display: "flex", alignItems: "center", gap: "2px", fontSize: "0.75rem", color: "var(--accent-emerald)", fontWeight: "600" }}>
              <Battery size={13} /> {kneeState.battery}%
            </span>
          )}
        </div>

        {/* Chest Belt Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <Heart size={15} style={{ color: "var(--accent-rose)" }} />
          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "500" }}>Chest:</span>
          <SensorStatusBadge status={chestState.status} />
          {chestState.connected && (
            <span style={{ display: "flex", alignItems: "center", gap: "2px", fontSize: "0.75rem", color: "var(--accent-emerald)", fontWeight: "600" }}>
              <Battery size={13} /> {chestState.battery}%
            </span>
          )}
        </div>

        {/* Offline Engine Indicator */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "0.35rem",
          fontSize: "0.75rem",
          fontWeight: "500",
          color: backendOnline ? "var(--accent-emerald)" : "var(--accent-amber)"
        }}>
          <Wifi size={13} />
          <span>{backendOnline ? "Local Core Online" : "Local Engine Standby"}</span>
        </div>

        {/* Theme Toggle (Light / Dark) */}
        <button
          onClick={toggleTheme}
          className="btn btn-secondary"
          style={{
            padding: "0.35rem 0.65rem",
            fontSize: "0.75rem"
          }}
          title={theme === "light" ? "Switch to Dark Theme" : "Switch to Light Theme"}
        >
          {theme === "light" ? (
            <>
              <Moon size={14} style={{ color: "var(--accent-blue)" }} />
              <span>Dark Mode</span>
            </>
          ) : (
            <>
              <Sun size={14} style={{ color: "var(--accent-amber)" }} />
              <span>Light Mode</span>
            </>
          )}
        </button>

        {/* Laboratory Simulator Switch */}
        <button
          onClick={() => toggleSimulation(!simulationMode)}
          className="btn btn-secondary"
          style={{
            padding: "0.35rem 0.75rem",
            fontSize: "0.75rem",
            borderColor: simulationMode ? "var(--accent-cyan)" : "var(--border-color)",
            background: simulationMode ? "rgba(2, 132, 199, 0.1)" : "var(--bg-elevated)",
            color: simulationMode ? "var(--accent-cyan)" : "var(--text-secondary)",
            fontWeight: "600"
          }}
          title="Toggle Laboratory Test Telemetry Stream when physical ESP32 wearables are not yet powered on"
        >
          <SlidersHorizontal size={13} />
          {simulationMode ? "Simulation: ON" : "Hardware Simulator: OFF"}
        </button>
      </div>
    </header>
  );
}
