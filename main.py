"""
Smart Cardiac Chest Belt - Real-Time Physiological Monitoring System
Application entry point. Safe for standalone execution, PyInstaller bundling,
and Spyder / interactive IPython environments.
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import config
from database.database import db
from ui.dashboard import DashboardWindow


def main():
    # 1. Initialize SQLite Database Schema
    db.init_database()

    # 2. Enable High-DPI Scaling for crisp desktop typography
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 3. Safe QApplication instantiation for Spyder & interactive kernels
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    else:
        owns_app = False

    app.setApplicationName(config.PROJECT_TITLE)
    app.setOrganizationName("SmartCardiac")

    # 4. Instantiate and Display Primary Dashboard
    window = DashboardWindow()
    window.show()

    # 5. Execute Event Loop safely
    if owns_app:
        sys.exit(app.exec())
    else:
        app.exec()


if __name__ == "__main__":
    main()
