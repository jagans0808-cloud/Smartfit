import React from "react";
import { ShieldAlert } from "lucide-react";

export default function MedicalDisclaimer() {
  return (
    <div className="notice-box" style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem" }}>
      <ShieldAlert size={18} style={{ color: "var(--accent-amber)", flexShrink: 0, marginTop: "2px" }} />
      <div>
        <strong style={{ color: "var(--accent-amber)" }}>Research Prototype — Not a Medical Diagnostic Device:</strong>{" "}
        SmartFit provides real-time AI-assisted exercise movement classification and functional screening support. It is designed for fitness monitoring, rehabilitation research, and athletic tracking. It does not replace certified clinical radiological diagnosis.
      </div>
    </div>
  );
}
