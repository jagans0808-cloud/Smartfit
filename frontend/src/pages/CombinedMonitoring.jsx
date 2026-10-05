import React, { useState, useEffect } from "react";
import { useSmartFit } from "../context/SmartFitContext";
import SensorStatusBadge from "../components/SensorStatusBadge";
import ECGWaveformChart from "../components/ECGWaveformChart";
import KneeAngleChart from "../components/KneeAngleChart";
import PlantarPressureVisualizer from "../components/PlantarPressureVisualizer";
import JointFlexionGauge from "../components/JointFlexionGauge";
import MedicalDisclaimer from "../components/MedicalDisclaimer";
import { 
  Layers, Play, Square, Save, Activity, Heart, 
  Clock, CheckCircle2, AlertTriangle, Vibrate
} from "lucide-react";

export default function CombinedMonitoring({ setActiveTab }) {
  const { 
    activePatient, kneeState, chestState, 
    aiLive, ecgBuffer, kneeAngleBuffer,
    triggerVibration, saveExerciseSession
  } = useSmartFit();

  const isKneeReceiving = kneeState.status === "RECEIVING_DATA";
  const isChestReceiving = chestState.status === "RECEIVING_DATA";
  const isSynchronized = isKneeReceiving && isChestReceiving;

  // Session recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [sessionSavedMsg, setSessionSavedMsg] = useState(null);

  useEffect(() => {
    let interval = null;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  const handleStartSession = () => {
    setIsRecording(true);
    setSessionSavedMsg(null);
  };

  const handleStopAndSave = async () => {
    setIsRecording(false);
    if (!activePatient) return;

    const sessionPayload = {
      patient_id: activePatient.patient_id,
      exercise_name: aiLive.exercise_name || "Squats",
      rep_count: aiLive.rep_count || 0,
      duration_seconds: Math.max(1, recordingSeconds),
      form_score: aiLive.form_score || 85.0,
      knee_rom: 75.0,
      avg_heart_rate: chestState.heart_rate || 78.0,
      avg_spo2: chestState.spo2 || 98.0,
      features: {
        knee_angle_mean: kneeState.knee_angle || 165.0,
        flex_mean: kneeState.flex_sensor || 30.0,
        heel_pressure: kneeState.heel_pressure || 50.0,
        forefoot_pressure: kneeState.forefoot_pressure || 50.0,
        trunk_tilt: chestState.trunk_tilt || 10.0
      },
      classification_result: {
        exercise_name: aiLive.exercise_name || "Squats",
        confidence: aiLive.confidence || 98.0,
        algorithm: "Random Forest Classifier (Scikit-Learn)",
        model_version: "SmartFit-RF-v1.0"
      },
      notes: "Synchronized dual-wearable session recorded from Smart Knee Band and Smart Chest Belt."
    };

    const res = await saveExerciseSession(sessionPayload);
    if (res) {
      setSessionSavedMsg(`Session #${res.session_id} saved successfully!`);
    }
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${rem.toString().padStart(2, "0")}`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Header and Recording Controls */}
      <div className="card" style={{
        background: "var(--banner-bg)",
        border: "1px solid var(--border-color)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>Synchronized Combined Monitoring</h2>
              {isSynchronized ? (
                <span className="badge badge-connected">Dual-Wearable Time-Aligned</span>
              ) : (
                <span className="badge badge-waiting">Partial / Sensor Standby</span>
              )}
            </div>
            <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
              Knee Band (Kinematics & Plantar Load) + Chest Belt (ECG & Biometrics) streaming simultaneously.
            </p>
          </div>

          {/* Recording Timer & Buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {isRecording && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.35rem 0.75rem",
                background: "rgba(244, 63, 94, 0.15)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                borderRadius: "0.4rem",
                color: "var(--accent-rose)",
                fontWeight: "700",
                fontFamily: "var(--font-mono)"
              }}>
                <span className="pulse-dot rose"></span>
                <Clock size={15} />
                <span>REC {formatTime(recordingSeconds)}</span>
              </div>
            )}

            {!isRecording ? (
              <button
                className="btn btn-cyan"
                onClick={handleStartSession}
                disabled={!isKneeReceiving && !isChestReceiving}
              >
                <Play size={15} />
                Start Multimodal Session
              </button>
            ) : (
              <button
                className="btn btn-primary"
                onClick={handleStopAndSave}
              >
                <Square size={15} />
                Stop & Save Session
              </button>
            )}

            <button
              className="btn btn-secondary"
              onClick={() => triggerVibration(7, 800, "Multimodal Cue")}
              title="Actuate Knee Band Vibration Motor"
            >
              <Vibrate size={15} style={{ color: "var(--accent-amber)" }} />
              Haptic Cue
            </button>
          </div>
        </div>

        {sessionSavedMsg && (
          <div style={{
            marginTop: "0.85rem",
            padding: "0.5rem 0.75rem",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "0.35rem",
            color: "var(--accent-emerald)",
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem"
          }}>
            <CheckCircle2 size={16} />
            <span>{sessionSavedMsg}</span>
          </div>
        )}
      </div>

      {/* Synchronized Dual Telemetry Row */}
      <div className="grid-2">
        {/* Chest Belt Live Telemetry */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Heart size={18} style={{ color: "var(--accent-rose)" }} />
              Smart Chest Belt (Cardiac & Posture)
            </span>
            <SensorStatusBadge status={chestState.status} />
          </div>

          <ECGWaveformChart
            ecgBuffer={ecgBuffer}
            isReceiving={isChestReceiving}
            leadsOff={chestState.leads_off}
            heartRate={chestState.heart_rate}
            height={200}
          />

          <div className="grid-3" style={{ marginTop: "1rem" }}>
            <div className="stat-box">
              <span className="stat-label">Heart Rate</span>
              <div className="stat-value" style={{ color: "var(--accent-rose)", fontSize: "1.2rem" }}>
                {isChestReceiving && chestState.heart_rate !== null ? `${chestState.heart_rate}` : "—"}
                <span className="stat-unit">BPM</span>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-label">SpO2</span>
              <div className="stat-value" style={{ color: "var(--accent-emerald)", fontSize: "1.2rem" }}>
                {isChestReceiving && chestState.spo2 !== null ? `${chestState.spo2}` : "—"}
                <span className="stat-unit">%</span>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-label">Trunk Tilt</span>
              <div className="stat-value" style={{ color: "var(--accent-amber)", fontSize: "1.2rem" }}>
                {isChestReceiving && chestState.trunk_tilt !== null ? `${chestState.trunk_tilt}` : "—"}
                <span className="stat-unit">deg</span>
              </div>
            </div>
          </div>
        </div>

        {/* Knee Band Live Telemetry */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Activity size={18} style={{ color: "var(--accent-cyan)" }} />
              Smart Knee Band (Kinematics & Plantar)
            </span>
            <SensorStatusBadge status={kneeState.status} />
          </div>

          <KneeAngleChart
            angleBuffer={kneeAngleBuffer}
            isReceiving={isKneeReceiving}
            currentAngle={kneeState.knee_angle}
            height={200}
          />

          <div className="grid-3" style={{ marginTop: "1rem" }}>
            <div className="stat-box">
              <span className="stat-label">Knee Angle</span>
              <div className="stat-value" style={{ color: "var(--accent-cyan)", fontSize: "1.2rem" }}>
                {isKneeReceiving && kneeState.knee_angle !== null ? `${kneeState.knee_angle}` : "—"}
                <span className="stat-unit">deg</span>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-label">Joint Bending</span>
              <div className="stat-value" style={{ color: "var(--accent-purple)", fontSize: "1.2rem" }}>
                {isKneeReceiving && kneeState.flex_sensor !== null ? `${kneeState.flex_sensor}` : "—"}
                <span className="stat-unit">deg</span>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-label">Repetitions</span>
              <div className="stat-value" style={{ color: "var(--text-heading)", fontSize: "1.2rem" }}>
                {isKneeReceiving ? aiLive.rep_count : "—"}
                <span className="stat-unit">reps</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Plantar Load & Curvature Gauges */}
      <div className="grid-2">
        <div className="card">
          <PlantarPressureVisualizer
            heelPressure={kneeState.heel_pressure}
            forefootPressure={kneeState.forefoot_pressure}
            isReceiving={isKneeReceiving}
          />
        </div>
        <div className="card">
          <JointFlexionGauge
            flexSensor={kneeState.flex_sensor}
            isReceiving={isKneeReceiving}
          />
        </div>
      </div>

      <MedicalDisclaimer />
    </div>
  );
}
