import React, { useState } from "react";
import { SmartFitProvider } from "./context/SmartFitContext";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";

// Pages
import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import KneeBand from "./pages/KneeBand";
import ChestBelt from "./pages/ChestBelt";
import CombinedMonitoring from "./pages/CombinedMonitoring";
import AIAnalysis from "./pages/AIAnalysis";
import Reports from "./pages/Reports";
import DeviceHardware from "./pages/DeviceHardware";

function SmartFitApp() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const renderActiveTab = () => {
    switch (activeTab) {
      case "dashboard":
        return <Dashboard setActiveTab={setActiveTab} />;
      case "patients":
        return <Patients setActiveTab={setActiveTab} />;
      case "knee_band":
        return <KneeBand setActiveTab={setActiveTab} />;
      case "chest_belt":
        return <ChestBelt setActiveTab={setActiveTab} />;
      case "combined":
        return <CombinedMonitoring setActiveTab={setActiveTab} />;
      case "ai_analysis":
        return <AIAnalysis setActiveTab={setActiveTab} />;
      case "reports":
        return <Reports setActiveTab={setActiveTab} />;
      case "hardware":
        return <DeviceHardware setActiveTab={setActiveTab} />;
      default:
        return <Dashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-content">
        <Header />
        <main className="page-body">
          {renderActiveTab()}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <SmartFitProvider>
      <SmartFitApp />
    </SmartFitProvider>
  );
}
