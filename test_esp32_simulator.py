"""
Smart Cardiac Chest Belt - ESP32 WebSocket Simulator
Streams authentic physiological and biomechanical telemetry packets over local WebSocket (port 81)
for end-to-end testing and demonstration without physical ESP32 hardware attached.
Matches the firmware packet format in esp32/SmartCardiacBelt.ino.
"""

import time
import math
import json
import asyncio
import websockets

PORT = 81


async def handler(websocket):
    print(f"[Simulator] Client connected from {websocket.remote_address}")
    start_time = time.time()
    fall_trigger_time = 0.0

    try:
        while True:
            now = time.time()
            elapsed = now - start_time
            t_ms = int(now * 1000)

            # 1. ECG Biopotential Waveform (Realistic P-Q-R-S-T cardiac cycle)
            hr_bpm = 74.0 + 3.0 * math.sin(elapsed * 0.12)
            heart_period = 60.0 / hr_bpm
            phase = (elapsed % heart_period) / heart_period

            # AD8232 baseline ~2048 (12-bit ADC mid-scale)
            ecg_val = 2048.0 + 25.0 * math.sin(phase * 2 * math.pi)
            if 0.18 <= phase <= 0.22:    # Q wave dip
                ecg_val -= 130.0 * math.sin((phase - 0.18) / 0.04 * math.pi)
            elif 0.22 < phase <= 0.26:   # R wave spike
                ecg_val += 1350.0 * math.sin((phase - 0.22) / 0.04 * math.pi)
            elif 0.26 < phase <= 0.30:   # S wave dip
                ecg_val -= 220.0 * math.sin((phase - 0.26) / 0.04 * math.pi)
            elif 0.38 <= phase <= 0.52:  # T wave elevation
                ecg_val += 190.0 * math.sin((phase - 0.38) / 0.14 * math.pi)

            # 2. Temperature & SpO2
            temp = round(36.7 + 0.15 * math.sin(elapsed * 0.04), 1)
            spo2 = round(98.0 + 0.5 * math.sin(elapsed * 0.05), 1)

            # 3. Triaxial Accelerometer & Motion (MPU6050)
            # Baseline resting state: gravity ~9.8 m/s^2 on Z-axis
            accel_x = round(0.15 * math.sin(elapsed * 1.2), 2)
            accel_y = round(0.20 * math.cos(elapsed * 1.2), 2)
            accel_z = round(9.78 + 0.25 * math.sin(elapsed * 0.8), 2)

            gyro_x = round(0.02 * math.sin(elapsed), 2)
            gyro_y = round(0.03 * math.cos(elapsed), 2)
            gyro_z = round(0.01, 2)

            # Periodic simulated impact spike every 45 seconds to demonstrate fall detection
            fall_flag = False
            if int(elapsed) > 0 and int(elapsed) % 45 == 0 and (now - fall_trigger_time > 5.0):
                print(f"[Simulator] >>> Simulating sudden fall impact spike at t={elapsed:.1f}s")
                accel_z = 24.5  # Exceeds FALL_THRESHOLD (22.0 m/s^2)
                fall_flag = True
                fall_trigger_time = now

            packet = {
                "type": "sensor_data",
                "timestamp": t_ms,
                "ecg": int(ecg_val),
                "heart_rate": int(hr_bpm),
                "spo2": spo2,
                "temperature": temp,
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "gyro_x": gyro_x,
                "gyro_y": gyro_y,
                "gyro_z": gyro_z,
                "fall": fall_flag
            }

            await websocket.send(json.dumps(packet))
            await asyncio.sleep(0.04)  # 25 Hz telemetry stream

    except websockets.exceptions.ConnectionClosed:
        print("[Simulator] Client disconnected.")


async def main():
    print("=" * 65)
    print("  SMART CARDIAC CHEST BELT - ESP32 WebSocket Simulator")
    print(f"  Broadcasting on ws://127.0.0.1:{PORT} (Port {PORT})")
    print("=" * 65)
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
