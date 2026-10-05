"""
Smart Cardiac Chest Belt - Comprehensive System Validation Suite
Automated verification for syntax, module imports, SQLite schema,
DSP bandpass filtering, vitals tracking, fall detection, PDF compilation,
CSV export, and headless Qt GUI instantiation.
"""

import sys
import os
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config


def test_syntax_and_imports():
    print("[1/6] Testing syntax and module imports...")
    import config
    import communication.websocket_client
    import processing.ecg
    import processing.heart_rate
    import processing.fall_detection
    import database.database
    import reports.report
    import ui.styles
    import ui.dashboard
    import ui.main_window
    import main
    print("  -> All core modules imported successfully with zero errors.")


def test_database_and_records():
    print("[2/6] Testing SQLite database initialization, telemetry batching, and CSV export...")
    from database.database import db

    db.init_database()
    sid = db.start_session()
    assert sid is not None and sid > 0, "Session initiation failed."

    # Batch insert sample telemetry records
    sample_batch = [
        {
            "timestamp": int(time.time() * 1000) + i * 40,
            "ecg": 2048 + (500 if i % 10 == 0 else 0),
            "heart_rate": 75 + (i % 3),
            "rr_interval": 800.0,
            "temperature": 36.8,
            "accel_x": 0.12,
            "accel_y": 0.25,
            "accel_z": 9.81,
            "fall": 1 if i == 15 else 0
        }
        for i in range(30)
    ]
    db.log_sensor_data_batch(sid, sample_batch)

    # Log alerts
    db.log_alert(sid, "TEST_ALERT", "Automated verification alert", "INFO")
    db.log_alert(sid, "FALL_DETECTED", "Impact spike detected: 24.5 m/s²", "CRITICAL")

    # End session
    db.end_session(
        session_id=sid,
        duration=12.5,
        avg_hr=76.2,
        min_hr=75.0,
        max_hr=78.0,
        avg_rr=800.0,
        avg_temp=36.8,
        max_temp=36.9,
        fall_count=1
    )

    session_rec = db.get_session(sid)
    assert session_rec is not None, "Failed to retrieve session record."
    assert session_rec["fall_count"] == 1, "Fall count mismatch in session record."

    df = db.get_session_sensor_data(sid)
    assert len(df) == 30, f"Expected 30 sensor records, got {len(df)}."

    alerts = db.get_session_alerts(sid)
    assert len(alerts) >= 2, f"Expected at least 2 alerts, got {len(alerts)}."

    csv_path = os.path.join(config.DATA_DIR, f"test_session_{sid}.csv")
    csv_ok = db.export_session_to_csv(sid, csv_path)
    assert csv_ok and os.path.exists(csv_path), "CSV export failed."
    os.remove(csv_path)

    print("  -> Database CRUD, batch insertion, alerts log, and CSV export passed.")
    return sid


def test_signal_processing_and_vitals():
    print("[3/6] Testing ECG filtering and physiological vitals tracking...")
    from processing.ecg import ECGProcessor
    from processing.heart_rate import VitalSignTracker

    proc = ECGProcessor(sample_rate=250)
    qualities = []
    for i in range(200):
        val = 2048.0 + 100.0 * ((i % 25) - 12)
        filt, q, hr, rr = proc.add_sample(val, int(time.time() * 1000) + i * 4)
        qualities.append(q)

    assert any(q in ["GOOD SIGNAL", "POOR SIGNAL"] for q in qualities)

    tracker = VitalSignTracker()
    alerts = tracker.update(hr=48, rr=1250, temp=36.5)  # Bradycardia (< 50)
    assert any(a["alert_type"] == "HEART_RATE" for a in alerts), "Bradycardia alert failed."

    alerts = tracker.update(hr=135, rr=440, temp=38.6)  # Tachycardia (> 120) and Fever (> 38.0)
    assert tracker.avg_hr is not None and tracker.avg_hr > 0
    assert tracker.max_temp == 38.6

    print("  -> DSP IIR filtering, quality estimation, and vital threshold alarms passed.")


def test_motion_and_fall_detection():
    print("[4/6] Testing MPU6050 motion level classification and impact fall detection...")
    from processing.fall_detection import MotionAndFallDetector

    detector = MotionAndFallDetector()

    # 1. Normal resting state (gravity ~ 9.8 m/s^2 on Z)
    motion, fall_alert = detector.evaluate(ax=0.1, ay=0.1, az=9.8, raw_fall_flag=False)
    assert motion["level"] == "LOW"
    assert not motion["is_fall"]
    assert fall_alert is None

    # 2. Sudden impact spike exceeding FALL_THRESHOLD (22.0 m/s^2)
    motion, fall_alert = detector.evaluate(ax=2.0, ay=3.0, az=23.5, raw_fall_flag=False)
    assert motion["is_fall"] is True
    assert motion["fall_count"] == 1
    assert fall_alert is not None
    assert fall_alert["severity"] == "CRITICAL"

    print("  -> Motion categorization and rule-based fall impact detection passed.")


def test_pdf_report_generation(session_id: int):
    print("[5/6] Testing clinical PDF report compilation...")
    from reports.report import report_gen

    pdf_path = report_gen.generate_pdf(session_id)
    assert pdf_path is not None, "PDF generation returned None."
    assert os.path.exists(pdf_path), f"PDF file not found at: {pdf_path}"
    assert os.path.getsize(pdf_path) > 1000, "PDF file is suspiciously small or empty."
    print(f"  -> PDF report compiled successfully ({os.path.getsize(pdf_path)} bytes): {os.path.basename(pdf_path)}")


def test_headless_gui_startup():
    print("[6/6] Testing headless GUI startup and telemetry dispatch...")
    from PySide6.QtWidgets import QApplication
    from ui.dashboard import DashboardWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = DashboardWindow()
    window.show()

    # Simulate dispatching a valid telemetry packet
    sim_packet = {
        "type": "sensor_data",
        "timestamp": int(time.time() * 1000),
        "ecg": 2048,
        "heart_rate": 78,
        "temperature": 36.7,
        "accel_x": 0.1,
        "accel_y": 0.2,
        "accel_z": 9.8,
        "fall": False
    }
    window._on_telemetry_received(sim_packet)
    window._update_gui()

    window.ws_thread.stop()
    window.close()
    app.processEvents()
    print("  -> DashboardWindow instantiated, rendered, and closed cleanly with zero errors.")


def run_all_tests():
    print("=" * 70)
    print("  SMART CARDIAC CHEST BELT - COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 70)

    test_syntax_and_imports()
    sid = test_database_and_records()
    test_signal_processing_and_vitals()
    test_motion_and_fall_detection()
    test_pdf_report_generation(sid)
    test_headless_gui_startup()

    print("=" * 70)
    print("  >>> ALL 6/6 VALIDATION TESTS PASSED SUCCESSFULLY! <<<")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
