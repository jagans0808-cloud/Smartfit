"""
Smart Cardiac Chest Belt - Modern Medical Light Theme Stylesheet
Executive Clinical Telemetry Light Theme.
Features crisp white cards, clean slate backgrounds, high-contrast typography,
and unmistakable visual alerts for physiological and fall events.
"""

APP_STYLESHEET = """
/* ==================== GLOBAL BASE ==================== */
QMainWindow, QWidget#CentralWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Inter", "Roboto", sans-serif;
    font-size: 13px;
    letter-spacing: 0.15px;
}

/* ==================== TOP HEADER ==================== */
QFrame#HeaderFrame {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 24px;
    min-height: 56px;
}

QLabel#AppTitleLabel {
    color: #0284c7;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 1.2px;
}

QLabel#AppSubtitleLabel {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QLabel#DisclaimerLabel {
    color: #94a3b8;
    font-size: 11px;
    font-style: italic;
    font-weight: 500;
    padding: 4px 10px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}

/* ==================== CONNECTION CONTROL STRIP ==================== */
QFrame#ConnectionBar {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px 16px;
}

QLabel.BarLabel {
    color: #475569;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Status Badges */
QLabel.StatusBadge {
    padding: 5px 14px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}

QLabel#BadgeConnected {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
}

QLabel#BadgeConnecting {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fcd34d;
}

QLabel#BadgeReconnecting {
    background-color: #ffedd5;
    color: #c2410c;
    border: 1px solid #fdba74;
}

QLabel#BadgeDisconnected {
    background-color: #ffe4e6;
    color: #be123c;
    border: 1px solid #fda4af;
}

QLabel#BadgeRecording {
    background-color: #eff6ff;
    color: #0284c7;
    border: 1px solid #bfdbfe;
}

QLabel#BadgeIdle {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
}

/* ==================== TELEMETRY CARDS ==================== */
QFrame.CardFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 16px;
}

QFrame.CardFrame:hover {
    border: 1px solid #cbd5e1;
}

/* Fall Detection Specific Card Frame */
QFrame#FallCardNormal {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 16px;
}

QFrame#FallCardAlert {
    background-color: #fef2f2;
    border: 2px solid #ef4444;
    border-radius: 12px;
    padding: 14px 16px;
}

QLabel.CardTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

QLabel.CardValue {
    color: #0f172a;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    font-family: "Segoe UI", "Inter", sans-serif;
    margin: 3px 0px;
}

QLabel.CardUnit {
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
}

QLabel.CardSubtext {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
}

/* Metric Status Pills */
QLabel.MetricPill {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    border-radius: 5px;
    padding: 3px 8px;
    text-transform: uppercase;
}

QLabel#PillNormal {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #bbf7d0;
}

QLabel#PillWarning {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
}

QLabel#PillCritical {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
}

QLabel#PillOffline {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
}

/* ==================== BUTTONS ==================== */
QPushButton.PrimaryButton {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid #0369a1;
    border-radius: 7px;
    padding: 9px 18px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

QPushButton.PrimaryButton:hover {
    background-color: #0369a1;
    border-color: #0284c7;
}

QPushButton.PrimaryButton:pressed {
    background-color: #075985;
}

QPushButton.PrimaryButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

QPushButton.SuccessButton {
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #047857;
    border-radius: 7px;
    padding: 9px 18px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

QPushButton.SuccessButton:hover {
    background-color: #047857;
    border-color: #059669;
}

QPushButton.SuccessButton:pressed {
    background-color: #065f46;
}

QPushButton.SuccessButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

QPushButton.DangerButton {
    background-color: #dc2626;
    color: #ffffff;
    border: 1px solid #b91c1c;
    border-radius: 7px;
    padding: 9px 18px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

QPushButton.DangerButton:hover {
    background-color: #b91c1c;
    border-color: #dc2626;
}

QPushButton.DangerButton:pressed {
    background-color: #991b1b;
}

QPushButton.DangerButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

QPushButton.SecondaryButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 9px 16px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton.SecondaryButton:hover {
    background-color: #f8fafc;
    color: #0f172a;
    border-color: #94a3b8;
}

QPushButton.SecondaryButton:disabled {
    background-color: #f8fafc;
    color: #cbd5e1;
    border-color: #e2e8f0;
}

/* ==================== FORM INPUTS ==================== */
QLineEdit, QSpinBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #0284c7;
    background-color: #ffffff;
}

/* ==================== ALERTS LIST ==================== */
QListWidget#AlertsList {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px;
    font-size: 12px;
}

QListWidget#AlertsList::item {
    padding: 6px 8px;
    border-bottom: 1px solid #f1f5f9;
    border-radius: 4px;
}

QListWidget#AlertsList::item:hover {
    background-color: #f8fafc;
}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {
    background-color: #f8fafc;
    width: 7px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
