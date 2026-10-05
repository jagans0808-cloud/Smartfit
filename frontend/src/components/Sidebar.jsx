import React from "react";
import { 
  LayoutDashboard, Users, Activity, HeartPulse, 
  Layers, Cpu, FileText, Radio, ShieldAlert
} from "lucide-react";

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "patients", label: "Patients", icon: Users },
    { id: "knee_band", label: "Smart Knee Band", icon: Activity },
    { id: "chest_belt", label: "Smart Chest Belt", icon: HeartPulse },
    { id: "combined", label: "Combined Monitoring", icon: Layers },
    { id: "ai_analysis", label: "AI/ML Analysis", icon: Cpu },
    { id: "reports", label: "Reports", icon: FileText },
    { id: "hardware", label: "Hardware & Setup", icon: Radio }
  ];

  return (
    <aside style={{
      width: "250px",
      background: "var(--bg-secondary)",
      borderRight: "1px solid var(--border-color)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      padding: "1.25rem 0.75rem",
      flexShrink: 0
    }} className="sidebar">
      <div>
        <div style={{
          padding: "0.5rem 0.75rem 1rem",
          fontSize: "0.75rem",
          fontWeight: "700",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "var(--text-muted)"
        }}>
          System Navigation
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          {menuItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.65rem 0.85rem",
                  borderRadius: "0.5rem",
                  border: "none",
                  cursor: "pointer",
                  textAlign: "left",
                  width: "100%",
                  fontSize: "0.875rem",
                  fontWeight: isActive ? "600" : "500",
                  color: isActive ? "var(--accent-cyan)" : "var(--text-secondary)",
                  background: isActive ? "rgba(2, 132, 199, 0.08)" : "transparent",
                  borderLeft: isActive ? "3px solid var(--accent-cyan)" : "3px solid transparent",
                  transition: "all 0.15s ease"
                }}
              >
                <Icon size={18} style={{ color: isActive ? "var(--accent-cyan)" : "inherit" }} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Safety & Prototype Note */}
      <div style={{
        padding: "0.85rem",
        borderRadius: "0.5rem",
        background: "var(--bg-card)",
        border: "1px solid var(--border-color)",
        fontSize: "0.7rem",
        color: "var(--text-muted)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", color: "var(--accent-amber)", fontWeight: "600", marginBottom: "0.3rem" }}>
          <ShieldAlert size={14} />
          <span>Research Prototype</span>
        </div>
        <div>
          SIH26213 SmartFit Platform. Not a clinical medical device.
        </div>
      </div>
    </aside>
  );
}
