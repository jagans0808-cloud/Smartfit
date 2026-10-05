"""
Smart Cardiac Chest Belt - Primary Dashboard Window
Consolidated, real-time medical monitoring dashboard.
Directly interfaces with ESP32 over Wi-Fi (ws://ESP32_IP:81), runs online digital
filtering, tracks physiological vitals, performs rule-based fall detection,
and logs sessions to SQLite with instant PDF report generation.
"""

import os
import time
import math
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

import pyqtgraph as pg

import config
from communication.websocket_client import WebSocketClientThread
from processing.ecg import ECGProcessor
from processing.heart_rate import VitalSignTracker
from processing.fall_detection import MotionAndFallDetector
from database.database import db
from reports.report import report_gen
from ui.styles import APP_STYLESHEET


class DashboardWindow(QMainWindow):
    """Primary Application Window for Smart Cardiac Chest Belt."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.PROJECT_TITLE} — {config.PROJECT_SUBTITLE}")
        self.resize(1320, 880)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(APP_STYLESHEET)

        # Core Processors & Detectors
        self.ecg_processor = ECGProcessor(sample_rate=config.ECG_SAMPLE_RATE)
        self.vitals_tracker = VitalSignTracker()
        self.motion_detector = MotionAndFallDetector()

        # Telemetry Buffers for Smooth GUI Rendering
        self.plot_buffer = deque([0.0] * config.MAX_GRAPH_POINTS, maxlen=config.MAX_GRAPH_POINTS)
        self.incoming_ecg_queue = deque(maxlen=2000)

        # Session Recording State
        self.is_monitoring = False
        self.current_session_id: Optional[int] = None
        self.session_start_time: float = 0.0
        self.session_elapsed_seconds: float = 0.0
        self.sensor_db_buffer: List[Dict[str, Any]] = []

        # Latest Telemetry Cache
        self.latest_raw_data: Dict[str, Any] = {}
        self.latest_motion_info: Dict[str, Any] = {}
        self.latest_quality = "NO SIGNAL"

        # Initialize User Interface
        self._init_ui()

        # Background WebSocket Client Thread
        self.ws_thread = WebSocketClientThread(self)
        self.ws_thread.status_changed.connect(self._on_ws_status_changed)
        self.ws_thread.data_received.connect(self._on_telemetry_received)
        self.ws_thread.error_occurred.connect(self._on_ws_error)
        self.ws_thread.start()

        # GUI Refresh Timers
        # 1. High-speed waveform and vitals render loop (~25 FPS)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_gui)
        self.render_timer.start(config.GRAPH_REFRESH_RATE_MS)

        # 2. Database batch persistence loop (every 1000 ms)
        self.db_timer = QTimer(self)
        self.db_timer.timeout.connect(self._flush_db_buffer)
        self.db_timer.start(1000)

        # 3. Session elapsed clock (every 1000 ms)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_session_clock)
        self.clock_timer.start(1000)

        self._log_alert("System initialized. Ready to connect to ESP32.", "INFO")

    def _init_ui(self):
        """Constructs the unified single-window dashboard layout."""
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 12, 18, 14)
        main_layout.setSpacing(12)

        # 1. Top Clinical Header
        main_layout.addWidget(self._create_header_widget())

        # 2. Connection Control Strip
        main_layout.addWidget(self._create_connection_bar())

        # 3. 6 Vital Telemetry Cards Grid
        main_layout.addWidget(self._create_vital_cards_grid())

        # 4. Middle Section: Real-time ECG Graph + Live Alerts Side-Panel
        middle_splitter = QSplitter(Qt.Horizontal)
        middle_splitter.setHandleWidth(8)
        middle_splitter.addWidget(self._create_ecg_graph_widget())
        middle_splitter.addWidget(self._create_alerts_panel_widget())
        middle_splitter.setStretchFactor(0, 7)  # 70% ECG Waveform
        middle_splitter.setStretchFactor(1, 3)  # 30% Alerts Log
        main_layout.addWidget(middle_splitter, stretch=1)

        # 5. Bottom Control & Action Bar
        main_layout.addWidget(self._create_bottom_bar())

    # ==================== UI BUILDERS ====================

    def _create_header_widget(self) -> QWidget:
        header = QFrame()
        header.setObjectName("HeaderFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(16)

        # Title and Subtitle
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel(config.PROJECT_TITLE)
        lbl_title.setObjectName("AppTitleLabel")
        lbl_sub = QLabel(config.PROJECT_SUBTITLE)
        lbl_sub.setObjectName("AppSubtitleLabel")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        layout.addLayout(title_box)

        layout.addStretch()

        # Disclaimer Pill
        lbl_disclaimer = QLabel(f"⚠️ {config.PROJECT_DISCLAIMER}")
        lbl_disclaimer.setObjectName("DisclaimerLabel")
        layout.addWidget(lbl_disclaimer)

        # Monitoring Status Badge
        self.badge_monitoring = QLabel("IDLE")
        self.badge_monitoring.setProperty("class", "StatusBadge")
        self.badge_monitoring.setObjectName("BadgeIdle")
        layout.addWidget(self.badge_monitoring)

        # WebSocket Connection Badge
        self.badge_connection = QLabel("DISCONNECTED")
        self.badge_connection.setProperty("class", "StatusBadge")
        self.badge_connection.setObjectName("BadgeDisconnected")
        layout.addWidget(self.badge_connection)

        return header

    def _create_connection_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("ConnectionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(14)

        # IP Target Input
        lbl_ip = QLabel("ESP32 IP:")
        lbl_ip.setProperty("class", "BarLabel")
        layout.addWidget(lbl_ip)

        self.input_ip = QLineEdit(config.DEFAULT_ESP32_IP)
        self.input_ip.setFixedWidth(130)
        self.input_ip.setToolTip("IP address of the ESP32 on your local Wi-Fi")
        layout.addWidget(self.input_ip)

        # Port Input
        lbl_port = QLabel("Port:")
        lbl_port.setProperty("class", "BarLabel")
        layout.addWidget(lbl_port)

        self.input_port = QLineEdit(str(config.WEBSOCKET_PORT))
        self.input_port.setFixedWidth(60)
        self.input_port.setToolTip("WebSocket server port (Default: 81)")
        layout.addWidget(self.input_port)

        # Connect / Disconnect Toggle Button
        self.btn_connect = QPushButton("CONNECT")
        self.btn_connect.setProperty("class", "PrimaryButton")
        self.btn_connect.clicked.connect(self._toggle_connection)
        layout.addWidget(self.btn_connect)

        layout.addSpacing(20)

        # Telemetry Counter Label
        self.lbl_telemetry_stat = QLabel("Packets: 0 | Latency: --")
        self.lbl_telemetry_stat.setProperty("class", "CardSubtext")
        layout.addWidget(self.lbl_telemetry_stat)

        layout.addStretch()

        # Quick Network Help
        lbl_help = QLabel("Local Wi-Fi: ws://ESP32_IP:81")
        lbl_help.setProperty("class", "CardSubtext")
        layout.addWidget(lbl_help)

        return bar

    def _create_vital_cards_grid(self) -> QWidget:
        grid_container = QWidget()
        layout = QGridLayout(grid_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Heart Rate Card
        self.card_hr, self.lbl_hr_val, self.lbl_hr_sub, self.lbl_hr_pill = self._build_card(
            "HEART RATE", "BPM", "--", "Avg: -- | Min: -- | Max: --", "OFFLINE"
        )
        layout.addWidget(self.card_hr, 0, 0)

        # 2. RR Interval Card
        self.card_rr, self.lbl_rr_val, self.lbl_rr_sub, self.lbl_rr_pill = self._build_card(
            "RR INTERVAL", "ms", "--", "Normal: 600 - 1200 ms", "OFFLINE"
        )
        layout.addWidget(self.card_rr, 0, 1)

        # 3. Body Temperature Card
        self.card_temp, self.lbl_temp_val, self.lbl_temp_sub, self.lbl_temp_pill = self._build_card(
            "BODY TEMPERATURE", "°C", "--", "Avg: -- °C | Max: -- °C", "OFFLINE"
        )
        layout.addWidget(self.card_temp, 0, 2)

        # 4. Motion Intensity Card
        self.card_motion, self.lbl_motion_val, self.lbl_motion_sub, self.lbl_motion_pill = self._build_card(
            "MOTION LEVEL", "m/s²", "--", "Ax: -- | Ay: -- | Az: --", "OFFLINE"
        )
        layout.addWidget(self.card_motion, 1, 0)

        # 5. Fall Detection Card (With prominent dynamic styling)
        self.card_fall = QFrame()
        self.card_fall.setObjectName("FallCardNormal")
        fall_layout = QVBoxLayout(self.card_fall)
        fall_layout.setContentsMargins(14, 12, 14, 12)
        fall_layout.setSpacing(4)

        f_top = QHBoxLayout()
        f_title = QLabel("FALL DETECTION")
        f_title.setProperty("class", "CardTitle")
        self.lbl_fall_pill = QLabel("0 FALLS")
        self.lbl_fall_pill.setProperty("class", "MetricPill")
        self.lbl_fall_pill.setObjectName("PillNormal")
        f_top.addWidget(f_title)
        f_top.addStretch()
        f_top.addWidget(self.lbl_fall_pill)
        fall_layout.addLayout(f_top)

        self.lbl_fall_val = QLabel("✓ NO FALL DETECTED")
        self.lbl_fall_val.setStyleSheet("font-size: 19px; font-weight: 800; color: #15803d; margin: 4px 0px;")
        fall_layout.addWidget(self.lbl_fall_val)

        self.lbl_fall_sub = QLabel(f"Impact Spike Limit: {config.FALL_THRESHOLD} m/s²")
        self.lbl_fall_sub.setProperty("class", "CardSubtext")
        fall_layout.addWidget(self.lbl_fall_sub)
        layout.addWidget(self.card_fall, 1, 1)

        # 6. ECG Signal Quality Card
        self.card_ecg, self.lbl_ecg_val, self.lbl_ecg_sub, self.lbl_ecg_pill = self._build_card(
            "ECG SIGNAL QUALITY", "", "NO SIGNAL", "Sampling: 250 Hz | Bandpass: 0.5-40Hz", "DISCONNECTED"
        )
        self.lbl_ecg_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #64748b; margin: 4px 0px;")
        layout.addWidget(self.card_ecg, 1, 2)

        return grid_container

    def _build_card(self, title: str, unit: str, default_val: str, default_sub: str, pill_text: str):
        card = QFrame()
        card.setProperty("class", "CardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 12, 14, 12)
        c_layout.setSpacing(3)

        top_row = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "CardTitle")
        lbl_pill = QLabel(pill_text)
        lbl_pill.setProperty("class", "MetricPill")
        lbl_pill.setObjectName("PillOffline")
        top_row.addWidget(lbl_title)
        top_row.addStretch()
        top_row.addWidget(lbl_pill)
        c_layout.addLayout(top_row)

        val_row = QHBoxLayout()
        val_row.setSpacing(6)
        lbl_val = QLabel(default_val)
        lbl_val.setProperty("class", "CardValue")
        val_row.addWidget(lbl_val)
        if unit:
            lbl_unit = QLabel(unit)
            lbl_unit.setProperty("class", "CardUnit")
            lbl_unit.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
            lbl_unit.setContentsMargins(0, 0, 0, 6)
            val_row.addWidget(lbl_unit)
        val_row.addStretch()
        c_layout.addLayout(val_row)

        lbl_sub = QLabel(default_sub)
        lbl_sub.setProperty("class", "CardSubtext")
        c_layout.addWidget(lbl_sub)

        return card, lbl_val, lbl_sub, lbl_pill

    def _create_ecg_graph_widget(self) -> QWidget:
        container = QFrame()
        container.setProperty("class", "CardFrame")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Graph Header Strip
        hdr = QHBoxLayout()
        lbl_graph_title = QLabel("REAL-TIME ELECTROCARDIOGRAM (AD8232)")
        lbl_graph_title.setProperty("class", "CardTitle")
        hdr.addWidget(lbl_graph_title)
        hdr.addStretch()

        self.lbl_ecg_live_status = QLabel("● NO SIGNAL")
        self.lbl_ecg_live_status.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 11px;")
        hdr.addWidget(self.lbl_ecg_live_status)
        layout.addLayout(hdr)

        # PyQtGraph Plot Widget
        pg.setConfigOption('background', '#ffffff')
        pg.setConfigOption('foreground', '#64748b')
        pg.setConfigOption('antialias', True)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=False, y=True)
        self.plot_widget.setLabel('left', 'Biopotential (ADC / mV)', color='#64748b', size='10pt')
        self.plot_widget.setLabel('bottom', 'Time Window (~3.0s at 250 Hz)', color='#64748b', size='10pt')
        self.plot_widget.setYRange(-1500, 2500, padding=0.1)

        # Emerald green clinical curve
        pen = pg.mkPen(color='#059669', width=2.0)
        self.ecg_curve = self.plot_widget.plot(pen=pen)
        layout.addWidget(self.plot_widget)

        return container

    def _create_alerts_panel_widget(self) -> QWidget:
        container = QFrame()
        container.setProperty("class", "CardFrame")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        lbl_alerts_title = QLabel("EVENT & ALERT AUDIT LOG")
        lbl_alerts_title.setProperty("class", "CardTitle")
        hdr.addWidget(lbl_alerts_title)
        hdr.addStretch()

        btn_clear_alerts = QPushButton("Clear")
        btn_clear_alerts.setProperty("class", "SecondaryButton")
        btn_clear_alerts.setFixedHeight(26)
        btn_clear_alerts.clicked.connect(self._clear_alerts)
        hdr.addWidget(btn_clear_alerts)
        layout.addLayout(hdr)

        # Alerts List Widget
        self.list_alerts = QListWidget()
        self.list_alerts.setObjectName("AlertsList")
        layout.addWidget(self.list_alerts)

        return container

    def _create_bottom_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("ConnectionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(14)

        # 1. Start Monitoring Button
        self.btn_start = QPushButton("▶ START MONITORING")
        self.btn_start.setProperty("class", "SuccessButton")
        self.btn_start.clicked.connect(self._start_monitoring)
        layout.addWidget(self.btn_start)

        # 2. Stop Monitoring Button
        self.btn_stop = QPushButton("⏹ STOP MONITORING")
        self.btn_stop.setProperty("class", "DangerButton")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_monitoring)
        layout.addWidget(self.btn_stop)

        layout.addSpacing(16)

        # 3. Session Elapsed Clock
        self.lbl_clock = QLabel("Session Duration: 00:00:00")
        self.lbl_clock.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f172a;")
        layout.addWidget(self.lbl_clock)

        layout.addStretch()

        # 4. Generate PDF Report Button
        self.btn_report = QPushButton("📑 GENERATE REPORT (PDF)")
        self.btn_report.setProperty("class", "PrimaryButton")
        self.btn_report.clicked.connect(self._generate_pdf_report)
        layout.addWidget(self.btn_report)

        # 5. Export CSV Button
        self.btn_csv = QPushButton("💾 EXPORT CSV")
        self.btn_csv.setProperty("class", "SecondaryButton")
        self.btn_csv.clicked.connect(self._export_csv)
        layout.addWidget(self.btn_csv)

        # 6. Clear Graph Button
        self.btn_clear_graph = QPushButton("⟳ CLEAR GRAPH")
        self.btn_clear_graph.setProperty("class", "SecondaryButton")
        self.btn_clear_graph.clicked.connect(self._clear_graph)
        layout.addWidget(self.btn_clear_graph)

        return bar

    # ==================== WEBSOCKET & TELEMETRY HANDLERS ====================

    def _toggle_connection(self):
        """Connects or disconnects the WebSocket background client."""
        if self.ws_thread._enabled and self.ws_thread._current_status in ["CONNECTED", "CONNECTING", "RECONNECTING"]:
            self.ws_thread.disconnect_socket()
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setProperty("class", "PrimaryButton")
            self.btn_connect.style().polish(self.btn_connect)
            self._log_alert("User initiated WebSocket disconnection.", "INFO")
        else:
            ip = self.input_ip.text().strip()
            try:
                port = int(self.input_port.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Invalid Port", "Please enter a valid numeric port (e.g. 81).")
                return

            self.ws_thread.set_target(ip, port)
            self.btn_connect.setText("DISCONNECT")
            self.btn_connect.setProperty("class", "DangerButton")
            self.btn_connect.style().polish(self.btn_connect)
            self._log_alert(f"Connecting to ESP32 at ws://{ip}:{port}...", "INFO")

    def _on_ws_status_changed(self, status: str):
        """Updates connection badges and logs status changes."""
        self.badge_connection.setText(status)
        if status == "CONNECTED":
            self.badge_connection.setObjectName("BadgeConnected")
            self.btn_connect.setText("DISCONNECT")
            self.btn_connect.setProperty("class", "DangerButton")
            self._log_alert(f"Successfully connected to ESP32 at {self.ws_thread.url}", "INFO")
        elif status == "CONNECTING":
            self.badge_connection.setObjectName("BadgeConnecting")
        elif status == "RECONNECTING":
            self.badge_connection.setObjectName("BadgeReconnecting")
        else:
            self.badge_connection.setObjectName("BadgeDisconnected")
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setProperty("class", "PrimaryButton")
            self.latest_quality = "NO SIGNAL"

        self.badge_connection.style().polish(self.badge_connection)
        self.btn_connect.style().polish(self.btn_connect)

    def _on_ws_error(self, err_msg: str):
        """Logs network error messages cleanly."""
        self._log_alert(f"Network error: {err_msg}", "WARNING")

    def _on_telemetry_received(self, data: Dict[str, Any]):
        """
        Processes real-time sensor telemetry packet from ESP32.
        Safely handles missing fields and prevents any crash.
        """
        self.latest_raw_data = data

        raw_ecg = data.get("ecg")
        raw_hr = data.get("heart_rate")
        raw_temp = data.get("temperature")
        raw_spo2 = data.get("spo2")
        ax = data.get("accel_x")
        ay = data.get("accel_y")
        az = data.get("accel_z")
        raw_fall = data.get("fall", False)
        t_ms = data.get("timestamp", int(time.time() * 1000))

        # 1. ECG Digital Signal Processing
        filtered_ecg, quality, est_hr, est_rr = self.ecg_processor.add_sample(raw_ecg, t_ms)
        self.latest_quality = quality
        if filtered_ecg is not None:
            self.incoming_ecg_queue.append(filtered_ecg)

        # 2. Physiological Vitals Processing
        best_hr = raw_hr if (raw_hr is not None and raw_hr > 0) else est_hr
        best_rr = est_rr
        vital_alerts = self.vitals_tracker.update(best_hr, best_rr, raw_temp, raw_spo2)
        for alert in vital_alerts:
            self._log_alert(alert["message"], alert["severity"], alert["alert_type"])

        # 3. Motion & Fall Detection
        motion_info, fall_alert = self.motion_detector.evaluate(ax, ay, az, raw_fall)
        self.latest_motion_info = motion_info
        if fall_alert:
            self._log_alert(fall_alert["message"], fall_alert["severity"], fall_alert["alert_type"])

        # 4. Session Persistence Buffer
        if self.is_monitoring and self.current_session_id is not None:
            record = {
                "timestamp": t_ms,
                "ecg": filtered_ecg,
                "heart_rate": self.vitals_tracker.current_hr,
                "rr_interval": self.vitals_tracker.current_rr,
                "temperature": self.vitals_tracker.current_temp,
                "accel_x": ax,
                "accel_y": ay,
                "accel_z": az,
                "fall": 1 if motion_info.get("is_fall") else 0
            }
            self.sensor_db_buffer.append(record)

    # ==================== GUI REFRESH LOOP (~25 FPS) ====================

    def _update_gui(self):
        """High-efficiency UI update loop. Decoupled from incoming network packets."""
        # 1. Drain incoming ECG samples to plot buffer
        points_added = False
        while self.incoming_ecg_queue:
            pt = self.incoming_ecg_queue.popleft()
            self.plot_buffer.append(pt)
            points_added = True

        if points_added:
            self.ecg_curve.setData(list(self.plot_buffer))

        # 2. Update Telemetry Packets Status
        pkt_count = self.ws_thread.packet_count
        self.lbl_telemetry_stat.setText(f"Packets: {pkt_count} | Queue: {len(self.incoming_ecg_queue)}")

        # 3. Update ECG Quality & Curve Header
        if self.ws_thread._current_status != "CONNECTED" or self.latest_quality == "NO SIGNAL":
            self.lbl_ecg_live_status.setText("● NO SIGNAL (WAITING FOR ESP32)")
            self.lbl_ecg_live_status.setStyleSheet("color: #94a3b8; font-weight: 700;")
            self.lbl_ecg_val.setText("NO SIGNAL")
            self.lbl_ecg_pill.setText("OFFLINE")
            self.lbl_ecg_pill.setObjectName("PillOffline")
        elif self.latest_quality == "POOR SIGNAL":
            self.lbl_ecg_live_status.setText("● POOR SIGNAL (CHECK LEADS)")
            self.lbl_ecg_live_status.setStyleSheet("color: #d97706; font-weight: 700;")
            self.lbl_ecg_val.setText("POOR SIGNAL")
            self.lbl_ecg_pill.setText("WARNING")
            self.lbl_ecg_pill.setObjectName("PillWarning")
        else:
            self.lbl_ecg_live_status.setText("● GOOD SIGNAL (ONLINE)")
            self.lbl_ecg_live_status.setStyleSheet("color: #059669; font-weight: 700;")
            self.lbl_ecg_val.setText("GOOD SIGNAL")
            self.lbl_ecg_pill.setText("NORMAL")
            self.lbl_ecg_pill.setObjectName("PillNormal")
        self.lbl_ecg_pill.style().polish(self.lbl_ecg_pill)

        # 4. Update Heart Rate Card
        hr = self.vitals_tracker.current_hr
        if hr is not None and hr > 0 and self.ws_thread._current_status == "CONNECTED":
            self.lbl_hr_val.setText(f"{hr:.0f}")
            avg_hr = self.vitals_tracker.avg_hr
            min_hr = self.vitals_tracker.min_hr
            max_hr = self.vitals_tracker.max_hr
            self.lbl_hr_sub.setText(f"Avg: {avg_hr or '--':.0f} | Min: {min_hr or '--':.0f} | Max: {max_hr or '--':.0f}")

            if hr < config.HEART_RATE_LOW:
                self.lbl_hr_pill.setText("BRADYCARDIA")
                self.lbl_hr_pill.setObjectName("PillCritical")
            elif hr > config.HEART_RATE_HIGH:
                self.lbl_hr_pill.setText("TACHYCARDIA")
                self.lbl_hr_pill.setObjectName("PillCritical")
            else:
                self.lbl_hr_pill.setText("NORMAL")
                self.lbl_hr_pill.setObjectName("PillNormal")
        else:
            self.lbl_hr_val.setText("--")
            self.lbl_hr_pill.setText("OFFLINE")
            self.lbl_hr_pill.setObjectName("PillOffline")
        self.lbl_hr_pill.style().polish(self.lbl_hr_pill)

        # 5. Update RR Interval Card
        rr = self.vitals_tracker.current_rr
        if rr is not None and rr > 0 and self.ws_thread._current_status == "CONNECTED":
            self.lbl_rr_val.setText(f"{rr:.0f}")
            avg_rr = self.vitals_tracker.avg_rr
            self.lbl_rr_sub.setText(f"Normative: 600 - 1200 ms | Avg: {avg_rr or '--':.0f} ms")
            if rr < config.RR_INTERVAL_MIN_MS or rr > config.RR_INTERVAL_MAX_MS:
                self.lbl_rr_pill.setText("IRREGULAR")
                self.lbl_rr_pill.setObjectName("PillWarning")
            else:
                self.lbl_rr_pill.setText("NORMAL")
                self.lbl_rr_pill.setObjectName("PillNormal")
        else:
            self.lbl_rr_val.setText("--")
            self.lbl_rr_pill.setText("OFFLINE")
            self.lbl_rr_pill.setObjectName("PillOffline")
        self.lbl_rr_pill.style().polish(self.lbl_rr_pill)

        # 6. Update Body Temperature Card
        temp = self.vitals_tracker.current_temp
        if temp is not None and temp > 0 and self.ws_thread._current_status == "CONNECTED":
            self.lbl_temp_val.setText(f"{temp:.1f}")
            avg_t = self.vitals_tracker.avg_temp
            max_t = self.vitals_tracker.max_temp
            self.lbl_temp_sub.setText(f"Avg: {avg_t or '--':.1f} °C | Max: {max_t or '--':.1f} °C")
            if temp > config.TEMPERATURE_HIGH:
                self.lbl_temp_pill.setText("FEVER")
                self.lbl_temp_pill.setObjectName("PillCritical")
            elif temp < config.TEMPERATURE_LOW:
                self.lbl_temp_pill.setText("HYPOTHERMIA")
                self.lbl_temp_pill.setObjectName("PillCritical")
            else:
                self.lbl_temp_pill.setText("NORMAL")
                self.lbl_temp_pill.setObjectName("PillNormal")
        else:
            self.lbl_temp_val.setText("--")
            self.lbl_temp_pill.setText("OFFLINE")
            self.lbl_temp_pill.setObjectName("PillOffline")
        self.lbl_temp_pill.style().polish(self.lbl_temp_pill)

        # 7. Update Motion Card
        if self.latest_motion_info and self.ws_thread._current_status == "CONNECTED":
            mag = self.latest_motion_info.get("magnitude", 0.0)
            lvl = self.latest_motion_info.get("level", "LOW")
            ax = self.latest_motion_info.get("accel_x", "--")
            ay = self.latest_motion_info.get("accel_y", "--")
            az = self.latest_motion_info.get("accel_z", "--")

            self.lbl_motion_val.setText(f"{mag:.2f}")
            self.lbl_motion_sub.setText(f"Ax: {ax} | Ay: {ay} | Az: {az}")
            self.lbl_motion_pill.setText(lvl)
            if lvl == "HIGH":
                self.lbl_motion_pill.setObjectName("PillWarning")
            else:
                self.lbl_motion_pill.setObjectName("PillNormal")
        else:
            self.lbl_motion_val.setText("--")
            self.lbl_motion_sub.setText("Ax: -- | Ay: -- | Az: --")
            self.lbl_motion_pill.setText("OFFLINE")
            self.lbl_motion_pill.setObjectName("PillOffline")
        self.lbl_motion_pill.style().polish(self.lbl_motion_pill)

        # 8. Update Fall Detection Card
        fall_active = self.motion_detector.is_fall_active
        fall_count = self.motion_detector.fall_count

        if fall_active:
            self.card_fall.setObjectName("FallCardAlert")
            self.lbl_fall_val.setText("🚨 FALL DETECTED!")
            self.lbl_fall_val.setStyleSheet("font-size: 21px; font-weight: 800; color: #dc2626; margin: 4px 0px;")
            self.lbl_fall_pill.setText(f"ALERT ({fall_count} FALLS)")
            self.lbl_fall_pill.setObjectName("PillCritical")
        else:
            self.card_fall.setObjectName("FallCardNormal")
            self.lbl_fall_val.setText("✓ NO FALL DETECTED")
            self.lbl_fall_val.setStyleSheet("font-size: 19px; font-weight: 800; color: #15803d; margin: 4px 0px;")
            self.lbl_fall_pill.setText(f"{fall_count} FALLS" if fall_count > 0 else "NORMAL")
            self.lbl_fall_pill.setObjectName("PillWarning" if fall_count > 0 else "PillNormal")

        self.card_fall.style().polish(self.card_fall)
        self.lbl_fall_pill.style().polish(self.lbl_fall_pill)

    # ==================== SESSION & RECORDING CONTROLS ====================

    def _start_monitoring(self):
        """Begins an active monitoring session and creates a database record."""
        self.current_session_id = db.start_session()
        self.is_monitoring = True
        self.session_start_time = time.time()
        self.session_elapsed_seconds = 0.0
        self.sensor_db_buffer.clear()

        # Reset trackers
        self.vitals_tracker.reset()
        self.motion_detector.reset()

        # UI updates
        self.badge_monitoring.setText("RECORDING")
        self.badge_monitoring.setObjectName("BadgeRecording")
        self.badge_monitoring.style().polish(self.badge_monitoring)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._log_alert(f"Monitoring Session #{self.current_session_id} started.", "INFO")

    def _stop_monitoring(self):
        """Finalizes the active monitoring session and saves aggregates."""
        if not self.is_monitoring or self.current_session_id is None:
            return

        self._flush_db_buffer()

        duration = time.time() - self.session_start_time
        avg_hr = self.vitals_tracker.avg_hr
        min_hr = self.vitals_tracker.min_hr
        max_hr = self.vitals_tracker.max_hr
        avg_rr = self.vitals_tracker.avg_rr
        avg_temp = self.vitals_tracker.avg_temp
        max_temp = self.vitals_tracker.max_temp
        falls = self.motion_detector.fall_count

        db.end_session(
            session_id=self.current_session_id,
            duration=duration,
            avg_hr=avg_hr,
            min_hr=min_hr,
            max_hr=max_hr,
            avg_rr=avg_rr,
            avg_temp=avg_temp,
            max_temp=max_temp,
            fall_count=falls
        )

        completed_sid = self.current_session_id
        self.is_monitoring = False
        self.current_session_id = None

        self.badge_monitoring.setText("IDLE")
        self.badge_monitoring.setObjectName("BadgeIdle")
        self.badge_monitoring.style().polish(self.badge_monitoring)

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self._log_alert(f"Monitoring Session #{completed_sid} ended ({duration:.1f}s, {falls} falls).", "INFO")

        # Prompt user to generate PDF report immediately
        reply = QMessageBox.question(
            self,
            "Session Completed",
            f"Session #{completed_sid} has been saved successfully.\n"
            f"Duration: {duration:.1f}s | Avg HR: {avg_hr or '--'} BPM | Falls: {falls}\n\n"
            "Would you like to generate and view the clinical PDF report now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._generate_pdf_for_session(completed_sid)

    def _update_session_clock(self):
        """Updates elapsed session duration display."""
        if self.is_monitoring:
            self.session_elapsed_seconds = time.time() - self.session_start_time
            m, s = divmod(int(self.session_elapsed_seconds), 60)
            h, m = divmod(m, 60)
            self.lbl_clock.setText(f"Session Duration: {h:02d}:{m:02d}:{s:02d}")
        else:
            self.lbl_clock.setText("Session Duration: 00:00:00")

    def _flush_db_buffer(self):
        """Flushes buffered sensor data to SQLite."""
        if self.sensor_db_buffer and self.current_session_id is not None:
            batch = list(self.sensor_db_buffer)
            self.sensor_db_buffer.clear()
            db.log_sensor_data_batch(self.current_session_id, batch)

    # ==================== REPORTS & EXPORT ====================

    def _generate_pdf_report(self):
        """Generates PDF report for current or most recently completed session."""
        target_sid = self.current_session_id
        if target_sid is None:
            # Query last session ID from database
            with db._lock:
                conn = db._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT id FROM sessions ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                conn.close()
                if row:
                    target_sid = row["id"]

        if not target_sid:
            QMessageBox.information(self, "No Sessions", "No monitoring session records found to report.")
            return

        self._generate_pdf_for_session(target_sid)

    def _generate_pdf_for_session(self, session_id: int):
        """Compiles and displays PDF report."""
        self._flush_db_buffer()
        try:
            pdf_path = report_gen.generate_pdf(session_id)
            if pdf_path and os.path.exists(pdf_path):
                self._log_alert(f"Generated PDF Report: {os.path.basename(pdf_path)}", "INFO")
                reply = QMessageBox.information(
                    self,
                    "Report Generated",
                    f"PDF Report successfully created:\n{pdf_path}\n\n"
                    "Would you like to open the report now?",
                    QMessageBox.Open | QMessageBox.Ok
                )
                if reply == QMessageBox.Open:
                    os.startfile(pdf_path)
            else:
                QMessageBox.warning(self, "Export Failed", f"Could not generate report for Session #{session_id}.")
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Error generating PDF: {e}")

    def _export_csv(self):
        """Exports session sensor telemetry to CSV."""
        target_sid = self.current_session_id
        if target_sid is None:
            with db._lock:
                conn = db._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT id FROM sessions ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                conn.close()
                if row:
                    target_sid = row["id"]

        if not target_sid:
            QMessageBox.information(self, "No Sessions", "No monitoring session records found to export.")
            return

        default_name = f"SmartCardiac_Session_{target_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Session Telemetry to CSV",
            os.path.join(config.DATA_DIR, default_name),
            "CSV Files (*.csv)"
        )
        if file_path:
            self._flush_db_buffer()
            success = db.export_session_to_csv(target_sid, file_path)
            if success:
                self._log_alert(f"Exported Session #{target_sid} to CSV: {os.path.basename(file_path)}", "INFO")
                QMessageBox.information(self, "CSV Export", f"Data exported successfully to:\n{file_path}")
            else:
                QMessageBox.warning(self, "CSV Export", "No sensor records available to export for this session.")

    def _clear_graph(self):
        """Resets waveform buffer and plot curve."""
        self.plot_buffer.clear()
        self.plot_buffer.extend([0.0] * config.MAX_GRAPH_POINTS)
        self.ecg_curve.setData(list(self.plot_buffer))
        self.ecg_processor.reset()
        self._log_alert("Waveform display buffers cleared.", "INFO")

    def _log_alert(self, message: str, severity: str = "INFO", alert_type: str = "SYSTEM"):
        """Logs an alert to UI list and database."""
        now_str = datetime.now().strftime("%H:%M:%S")

        icon = "ℹ️"
        if severity == "CRITICAL":
            icon = "🚨"
        elif severity == "WARNING":
            icon = "⚠️"

        item_text = f"[{now_str}] {icon} {message}"
        item = QListWidgetItem(item_text)

        if severity == "CRITICAL":
            item.setForeground(QColor("#dc2626"))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        elif severity == "WARNING":
            item.setForeground(QColor("#b45309"))

        self.list_alerts.addItem(item)
        self.list_alerts.scrollToBottom()

        # Save to database
        if self.current_session_id is not None:
            db.log_alert(self.current_session_id, alert_type, message, severity)

    def _clear_alerts(self):
        """Clears the alerts audit list."""
        self.list_alerts.clear()

    def closeEvent(self, event):
        """Cleans up background threads and active sessions on window close."""
        if self.is_monitoring:
            self._stop_monitoring()
        self.render_timer.stop()
        self.db_timer.stop()
        self.clock_timer.stop()
        self.ws_thread.stop()
        if event is not None:
            event.accept()
