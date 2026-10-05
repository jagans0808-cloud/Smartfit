import React from "react";
import { CheckCircle2, AlertCircle, Clock, WifiOff, Activity } from "lucide-react";

export default function SensorStatusBadge({ status, label }) {
  if (status === "RECEIVING_DATA") {
    return (
      <span className="badge badge-receiving">
        <span className="pulse-dot cyan"></span>
        <Activity size={12} />
        {label || "Receiving Data"}
      </span>
    );
  }

  if (status === "CONNECTED") {
    return (
      <span className="badge badge-connected">
        <span className="pulse-dot green"></span>
        <CheckCircle2 size={12} />
        {label || "Connected"}
      </span>
    );
  }

  if (status === "WAITING_FOR_SENSOR") {
    return (
      <span className="badge badge-waiting">
        <span className="pulse-dot amber"></span>
        <Clock size={12} />
        {label || "Waiting for Sensor"}
      </span>
    );
  }

  if (status === "SIGNAL_PROBLEM") {
    return (
      <span className="badge badge-alert">
        <span className="pulse-dot rose"></span>
        <AlertCircle size={12} />
        {label || "Signal Problem"}
      </span>
    );
  }

  if (status === "NO_DATA") {
    return (
      <span className="badge badge-waiting">
        <span className="pulse-dot amber"></span>
        <Clock size={12} />
        {label || "No Data"}
      </span>
    );
  }

  return (
    <span className="badge badge-disconnected">
      <span className="pulse-dot gray"></span>
      <WifiOff size={12} />
      {label || "Not Connected"}
    </span>
  );
}
