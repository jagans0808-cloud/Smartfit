import React, { useState } from "react";
import { useSmartFit } from "../context/SmartFitContext";
import { 
  Users, UserPlus, Search, Calendar, MapPin, 
  Phone, Activity, FileText, CheckCircle2, ChevronRight, X
} from "lucide-react";

export default function Patients({ setActiveTab }) {
  const { patients, activePatient, setActivePatient, registerPatient } = useSmartFit();

  const [searchQuery, setSearchQuery] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    contact: "",
    place: "",
    age: 30,
    gender: "Male",
    height: 170,
    weight: 70,
    pain_side: "Right"
  });
  const [submitting, setSubmitting] = useState(false);

  const filteredPatients = patients.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.patient_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRegister = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const result = await registerPatient(formData);
    setSubmitting(false);
    if (result.success) {
      setShowModal(false);
      setFormData({
        name: "",
        contact: "",
        place: "",
        age: 30,
        gender: "Male",
        height: 170,
        weight: 70,
        pain_side: "Right"
      });
    }
  };

  const bmi = activePatient ? (activePatient.weight / ((activePatient.height / 100) ** 2)).toFixed(1) : "—";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Top Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h2 style={{ fontSize: "1.35rem", fontWeight: "700" }}>Patient Management</h2>
          <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
            Register and manage clinical & athletic profiles for multi-sensor monitoring.
          </p>
        </div>
        <button
          className="btn btn-cyan"
          onClick={() => setShowModal(true)}
        >
          <UserPlus size={16} />
          Register New Patient
        </button>
      </div>

      {/* Main Grid: Directory & Active Profile */}
      <div className="grid-2">
        {/* Patient Directory */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Users size={18} style={{ color: "var(--accent-cyan)" }} />
              Patient Directory ({filteredPatients.length})
            </span>
            {/* Search Input */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              background: "var(--bg-primary)",
              padding: "0.3rem 0.6rem",
              borderRadius: "0.4rem",
              border: "1px solid var(--border-color)"
            }}>
              <Search size={14} style={{ color: "var(--text-muted)" }} />
              <input
                type="text"
                placeholder="Search by name or ID..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-primary)",
                  fontSize: "0.8rem",
                  outline: "none",
                  width: "140px"
                }}
              />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "450px", overflowY: "auto" }}>
            {filteredPatients.map(p => {
              const isSelected = activePatient?.patient_id === p.patient_id;
              const pBmi = (p.weight / ((p.height / 100) ** 2)).toFixed(1);
              return (
                <div
                  key={p.patient_id}
                  onClick={() => setActivePatient(p)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.75rem 0.85rem",
                    borderRadius: "0.5rem",
                    cursor: "pointer",
                    background: isSelected ? "var(--bg-elevated)" : "var(--bg-primary)",
                    border: isSelected ? "1px solid var(--accent-cyan)" : "1px solid var(--border-color)",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <strong style={{ fontSize: "0.95rem", color: isSelected ? "var(--accent-cyan)" : "var(--text-primary)" }}>
                        {p.name}
                      </strong>
                      <span className="badge badge-connected" style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem" }}>
                        {p.patient_id}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                      {p.gender}, {p.age} yrs • BMI: {pBmi} • Pain: {p.pain_side}
                    </div>
                  </div>
                  <ChevronRight size={16} style={{ color: isSelected ? "var(--accent-cyan)" : "var(--text-muted)" }} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Patient Profile & Clinical Baseline */}
        {activePatient && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <Activity size={18} style={{ color: "var(--accent-blue)" }} />
                Patient Biomechanical Baseline
              </span>
              <span className="badge badge-connected">{activePatient.patient_id}</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: "0.75rem",
                background: "var(--bg-primary)",
                padding: "0.85rem",
                borderRadius: "0.5rem",
                border: "1px solid var(--border-color)"
              }}>
                <div>
                  <span className="stat-label">Full Name</span>
                  <div style={{ fontWeight: "600" }}>{activePatient.name}</div>
                </div>
                <div>
                  <span className="stat-label">Contact</span>
                  <div style={{ fontWeight: "600" }}>{activePatient.contact || "—"}</div>
                </div>
                <div>
                  <span className="stat-label">Location</span>
                  <div style={{ fontWeight: "600" }}>{activePatient.place || "—"}</div>
                </div>
                <div>
                  <span className="stat-label">Age / Gender</span>
                  <div style={{ fontWeight: "600" }}>{activePatient.age} yrs, {activePatient.gender}</div>
                </div>
                <div>
                  <span className="stat-label">Height & Weight</span>
                  <div style={{ fontWeight: "600" }}>{activePatient.height} cm / {activePatient.weight} kg</div>
                </div>
                <div>
                  <span className="stat-label">Calculated BMI</span>
                  <div style={{ fontWeight: "700", color: "var(--accent-cyan)" }}>{bmi} kg/m²</div>
                </div>
                <div>
                  <span className="stat-label">Symptom Localization</span>
                  <div style={{ fontWeight: "600", color: "var(--accent-amber)" }}>{activePatient.pain_side} Knee</div>
                </div>
                <div>
                  <span className="stat-label">Registration Date</span>
                  <div style={{ fontWeight: "600", fontSize: "0.8rem" }}>{activePatient.created_at || "Baseline Active"}</div>
                </div>
              </div>

              {/* Action Buttons for this Patient */}
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <button
                  className="btn btn-cyan"
                  onClick={() => setActiveTab("knee_band")}
                  style={{ flex: 1 }}
                >
                  <Activity size={15} />
                  Knee Band Screening
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setActiveTab("combined")}
                  style={{ flex: 1 }}
                >
                  Combined Session
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setActiveTab("reports")}
                  style={{ flex: 1 }}
                >
                  <FileText size={15} />
                  Patient Report
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Patient Registration Modal */}
      {showModal && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.75)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
          padding: "1rem"
        }}>
          <div className="card" style={{ maxWidth: "520px", width: "100%", background: "var(--bg-secondary)" }}>
            <div className="card-header">
              <span className="card-title">
                <UserPlus size={18} style={{ color: "var(--accent-cyan)" }} />
                Register New Patient
              </span>
              <button
                onClick={() => setShowModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
              <div className="grid-2">
                <div>
                  <label className="stat-label">Full Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
                <div>
                  <label className="stat-label">Contact Number</label>
                  <input
                    type="text"
                    required
                    value={formData.contact}
                    onChange={e => setFormData({ ...formData, contact: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
              </div>

              <div className="grid-2">
                <div>
                  <label className="stat-label">Age</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={formData.age}
                    onChange={e => setFormData({ ...formData, age: parseInt(e.target.value) || 0 })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
                <div>
                  <label className="stat-label">Gender</label>
                  <select
                    value={formData.gender}
                    onChange={e => setFormData({ ...formData, gender: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid-2">
                <div>
                  <label className="stat-label">Height (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.height}
                    onChange={e => setFormData({ ...formData, height: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
                <div>
                  <label className="stat-label">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.weight}
                    onChange={e => setFormData({ ...formData, weight: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
              </div>

              <div className="grid-2">
                <div>
                  <label className="stat-label">Place / City</label>
                  <input
                    type="text"
                    value={formData.place}
                    onChange={e => setFormData({ ...formData, place: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  />
                </div>
                <div>
                  <label className="stat-label">Pain / Symptom Side</label>
                  <select
                    value={formData.pain_side}
                    onChange={e => setFormData({ ...formData, pain_side: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.35rem",
                      color: "var(--text-primary)"
                    }}
                  >
                    <option value="Right">Right</option>
                    <option value="Left">Left</option>
                    <option value="Bilateral">Bilateral</option>
                    <option value="None">None</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn btn-cyan"
                >
                  {submitting ? "Registering..." : "Save Patient"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
