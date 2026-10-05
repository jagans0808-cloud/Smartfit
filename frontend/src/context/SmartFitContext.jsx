import React, { createContext, useContext, useState, useEffect, useRef } from "react";

const SmartFitContext = createContext();

const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws/live";

export function SmartFitProvider({ children }) {
  const [patients, setPatients] = useState([
    {
      patient_id: "SF-1001",
      name: "Rohan Sharma",
      age: 28,
      gender: "Male",
      height: 176,
      weight: 74.5,
      pain_side: "Right",
      place: "New Delhi, India",
      contact: "9876543210"
    },
    {
      patient_id: "SF-1002",
      name: "Ananya Patel",
      age: 52,
      gender: "Female",
      height: 162,
      weight: 68.0,
      pain_side: "Bilateral",
      place: "Mumbai, India",
      contact: "9823456789"
    }
  ]);

  const [activePatient, setActivePatient] = useState(patients[0]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [simulationMode, setSimulationMode] = useState(false);

  // Knee Band Telemetry State
  const [kneeState, setKneeState] = useState({
    connected: false,
    battery: 0,
    vibration_motor: "IDLE",
    status: "NOT_CONNECTED",
    knee_angle: null,
    flex_sensor: null,
    heel_pressure: null,
    forefoot_pressure: null,
    pressure_imbalance: null,
    thigh_accel: null,
    shin_accel: null
  });

  // Chest Belt Telemetry State
  const [chestState, setChestState] = useState({
    connected: false,
    battery: 0,
    status: "NOT_CONNECTED",
    ecg_raw: null,
    heart_rate: null,
    spo2: null,
    trunk_tilt: null,
    leads_off: false,
    accel_x: null,
    accel_y: null,
    accel_z: null
  });

  // AI Live State
  const [aiLive, setAiLive] = useState({
    exercise_name: "No Data",
    confidence: 0,
    probabilities: {},
    rep_count: 0,
    form_score: 0,
    form_status: "Waiting for Sensor",
    vibration_alert: false,
    warnings: []
  });

  // Rolling buffers for real-time charts
  const [ecgBuffer, setEcgBuffer] = useState([]);
  const [kneeAngleBuffer, setKneeAngleBuffer] = useState([]);

  const wsRef = useRef(null);

  // Fetch Patients on Load
  const fetchPatients = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/patients`, {
        headers: { Authorization: "Bearer healthcare:ChangeMe123!" } // or public list
      });
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          setPatients(data);
          setActivePatient(prev => prev || data[0]);
        }
      }
    } catch {
      // Offline fallback already initialized with default seed
    }
  };

  // Check Backend Health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (res.ok) {
          const data = await res.json();
          setBackendOnline(true);
          setSimulationMode(data.simulation_mode);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };

    checkHealth();
    fetchPatients();
    const timer = setInterval(checkHealth, 5000);
    return () => clearInterval(timer);
  }, []);

  // WebSocket Connection
  useEffect(() => {
    let reconnectTimeout = null;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          setBackendOnline(true);
        };

        ws.onmessage = (event) => {
          try {
            const packet = JSON.parse(event.data);

            // 1. Process Knee Band
            if (packet.knee_band) {
              const kb = packet.knee_band;
              const kbData = kb.data;
              const isReceiving = kbData && kbData.status === "RECEIVING_DATA";

              setKneeState({
                connected: kb.connected,
                battery: kb.battery,
                vibration_motor: kb.vibration_motor || "IDLE",
                status: isReceiving ? "RECEIVING_DATA" : (kb.connected ? "NO_DATA" : "NOT_CONNECTED"),
                knee_angle: isReceiving ? kbData.knee_angle : null,
                flex_sensor: isReceiving ? kbData.flex_sensor : null,
                heel_pressure: isReceiving ? kbData.heel_pressure : null,
                forefoot_pressure: isReceiving ? kbData.forefoot_pressure : null,
                pressure_imbalance: isReceiving ? kbData.pressure_imbalance : null,
                thigh_accel: isReceiving ? kbData.thigh_accel : null,
                shin_accel: isReceiving ? kbData.shin_accel : null
              });

              if (isReceiving && kbData.knee_angle !== undefined) {
                setKneeAngleBuffer(prev => {
                  const updated = [...prev, kbData.knee_angle];
                  return updated.slice(-60); // Keep last 60 points
                });
              }
            }

            // 2. Process Chest Belt
            if (packet.chest_belt) {
              const cb = packet.chest_belt;
              const cbData = cb.data;
              const isReceiving = cbData && cbData.status === "RECEIVING_DATA";

              setChestState({
                connected: cb.connected,
                battery: cb.battery,
                status: isReceiving ? "RECEIVING_DATA" : (cb.connected ? "NO_DATA" : "NOT_CONNECTED"),
                ecg_raw: isReceiving ? cbData.ecg_raw : null,
                heart_rate: isReceiving ? cbData.heart_rate : null,
                spo2: isReceiving ? cbData.spo2 : null,
                trunk_tilt: isReceiving ? cbData.trunk_tilt : null,
                leads_off: isReceiving ? cbData.leads_off : false,
                accel_x: isReceiving ? cbData.accel_x : null,
                accel_y: isReceiving ? cbData.accel_y : null,
                accel_z: isReceiving ? cbData.accel_z : null
              });

              if (isReceiving && cbData.ecg_raw !== undefined) {
                setEcgBuffer(prev => {
                  const updated = [...prev, cbData.ecg_raw];
                  return updated.slice(-120); // Keep last 120 points for oscilloscope
                });
              }
            }

            // 3. Process AI Live
            if (packet.ai_live) {
              setAiLive(packet.ai_live);
            } else if (!packet.knee_band?.connected && !packet.chest_belt?.connected) {
              setAiLive({
                exercise_name: "No Data",
                confidence: 0,
                probabilities: {},
                rep_count: 0,
                form_score: 0,
                form_status: "Waiting for Sensor",
                vibration_alert: false,
                warnings: []
              });
            }

          } catch (e) {
            console.error("Failed to parse WebSocket packet:", e);
          }
        };

        ws.onclose = () => {
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Action: Toggle Hardware Simulation mode
  const toggleSimulation = async (enabled) => {
    try {
      const res = await fetch(`${API_BASE}/api/device/simulation-toggle?enabled=${enabled}`, {
        method: "POST"
      });
      if (res.ok) {
        setSimulationMode(enabled);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: "toggle_simulation", enabled }));
        }
      }
    } catch {
      setSimulationMode(enabled);
    }
  };

  // Action: Trigger Vibration Motor on Knee Band
  const triggerVibration = async (intensity = 5, durationMs = 600, reason = "Manual Cue") => {
    try {
      await fetch(`${API_BASE}/api/device/vibration-trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intensity, duration_ms: durationMs, reason })
      });
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "trigger_vibration" }));
      }
    } catch (e) {
      console.warn("Could not send vibration command:", e);
    }
  };

  // Action: Register new patient
  const registerPatient = async (patientData) => {
    try {
      const res = await fetch(`${API_BASE}/api/patients`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer healthcare:ChangeMe123!"
        },
        body: JSON.stringify(patientData)
      });
      if (res.ok) {
        const created = await res.json();
        const fullPatient = { ...patientData, patient_id: created.patient_id };
        setPatients(prev => [fullPatient, ...prev]);
        setActivePatient(fullPatient);
        return { success: true, patient: fullPatient };
      }
    } catch (err) {
      // Local fallback
      const localId = "SF-" + Date.now().toString().slice(-6);
      const fullPatient = { ...patientData, patient_id: localId };
      setPatients(prev => [fullPatient, ...prev]);
      setActivePatient(fullPatient);
      return { success: true, patient: fullPatient };
    }
    return { success: false };
  };

  // Action: Save screening
  const submitOAScreening = async (screeningData) => {
    try {
      const res = await fetch(`${API_BASE}/api/screenings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer healthcare:ChangeMe123!"
        },
        body: JSON.stringify(screeningData)
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.error(e);
    }
    return null;
  };

  // Action: Save Exercise Session
  const saveExerciseSession = async (sessionData) => {
    try {
      const res = await fetch(`${API_BASE}/api/exercise-sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer healthcare:ChangeMe123!"
        },
        body: JSON.stringify(sessionData)
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.error(e);
    }
    return null;
  };

  return (
    <SmartFitContext.Provider
      value={{
        patients,
        activePatient,
        setActivePatient,
        backendOnline,
        simulationMode,
        toggleSimulation,
        kneeState,
        chestState,
        aiLive,
        ecgBuffer,
        kneeAngleBuffer,
        triggerVibration,
        registerPatient,
        submitOAScreening,
        saveExerciseSession,
        fetchPatients
      }}
    >
      {children}
    </SmartFitContext.Provider>
  );
}

export function useSmartFit() {
  return useContext(SmartFitContext);
}
