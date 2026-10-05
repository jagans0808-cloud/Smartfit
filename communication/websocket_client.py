"""
Smart Cardiac Chest Belt - WebSocket Communication Client
Runs a persistent, non-blocking background daemon thread to maintain
reliable real-time communication with the ESP32 server over Wi-Fi (ws://ESP32_IP:81).
Uses Qt Signals for thread-safe UI telemetry dispatch.
"""

import time
import json
import socket
import logging
import threading
from typing import Optional

from PySide6.QtCore import QObject, Signal

import config

logger = logging.getLogger("SmartCardiac.WebSocket")


class WebSocketClientThread(QObject):
    """
    Background worker maintaining a persistent WebSocket connection to ESP32.
    Emits Qt signals to safely deliver incoming telemetry packets and status updates to GUI.
    Runs on a daemon thread for safe, non-blocking process lifecycle.
    """

    status_changed = Signal(str)       # "CONNECTED", "CONNECTING", "DISCONNECTED", "RECONNECTING"
    data_received = Signal(dict)       # Parsed JSON dictionary
    error_occurred = Signal(str)       # Human-readable error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lock = threading.Lock()
        self._is_running = False
        self._enabled = True
        self._ws: Optional[any] = None
        self._current_status = "DISCONNECTED"
        self._worker_thread: Optional[threading.Thread] = None

        self.ip = config.DEFAULT_ESP32_IP
        self.port = config.WEBSOCKET_PORT
        self.url = f"ws://{self.ip}:{self.port}"
        self.reconnect_interval = config.AUTO_RECONNECT_INTERVAL_S
        self.timeout = config.WEBSOCKET_TIMEOUT_S

        self.packet_count = 0
        self.last_packet_time = 0.0

    def start(self):
        """Starts the background worker thread."""
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._is_running = True
            self._enabled = True
            self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._worker_thread.start()

    def set_target(self, ip: str, port: int = config.WEBSOCKET_PORT):
        """Updates IP/Port target and reconnects."""
        with self._lock:
            self.ip = ip.strip()
            self.port = int(port)
            self.url = f"ws://{self.ip}:{self.port}"
            self._enabled = True
        self.reconnect()

    def disconnect_socket(self):
        """Manually disconnects and pauses auto-reconnect."""
        with self._lock:
            self._enabled = False
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass
        self._set_status("DISCONNECTED")

    def connect_socket(self):
        """Enables connection and initiates connect sequence."""
        with self._lock:
            self._enabled = True
        self.reconnect()

    def _run_loop(self):
        """Main thread loop with automatic reconnection and heartbeat."""
        import websocket

        while self._is_running:
            if not self._enabled:
                self._set_status("DISCONNECTED")
                time.sleep(0.2)
                continue

            self._set_status("CONNECTING")
            try:
                socket.setdefaulttimeout(self.timeout)
                self._ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self._ws.run_forever(
                    ping_interval=5,
                    ping_timeout=3
                )
            except Exception as e:
                self._on_error(self._ws, e)

            # Auto-reconnection backoff if still enabled & running
            if self._is_running and self._enabled:
                self._set_status("RECONNECTING")
                for _ in range(int(self.reconnect_interval * 10)):
                    if not self._is_running or not self._enabled:
                        break
                    time.sleep(0.1)

        self._set_status("DISCONNECTED")

    def _set_status(self, new_status: str):
        with self._lock:
            if self._current_status != new_status:
                self._current_status = new_status
                self.status_changed.emit(new_status)

    def _on_open(self, ws):
        self._set_status("CONNECTED")
        self.last_packet_time = time.time()

    def _on_message(self, ws, message):
        """Parses incoming JSON payload."""
        try:
            self.last_packet_time = time.time()
            self.packet_count += 1
            data = json.loads(message)
            if isinstance(data, dict):
                self.data_received.emit(data)
            else:
                self.error_occurred.emit("Received non-dictionary JSON message")
        except json.JSONDecodeError as err:
            self.error_occurred.emit(f"Invalid JSON packet: {err}")
        except Exception as e:
            self.error_occurred.emit(f"Error handling message: {e}")

    def _on_error(self, ws, error):
        err_msg = str(error) if error else "Network error"
        self.error_occurred.emit(f"Connection error: {err_msg}")

    def _on_close(self, ws, close_status_code, close_msg):
        if self._is_running and self._enabled:
            self._set_status("RECONNECTING")
        else:
            self._set_status("DISCONNECTED")

    def reconnect(self):
        """Forces immediate reconnection attempt."""
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass

    def stop(self):
        """Terminates background thread cleanly."""
        with self._lock:
            self._is_running = False
            self._enabled = False
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass


# Alias for backward compatibility
WebSocketClient = WebSocketClientThread
