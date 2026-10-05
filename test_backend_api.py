import urllib.request
import time
import subprocess
import json

print("Starting uvicorn server...")
proc = subprocess.Popen(
    [r"c:\SmartFit\backend\.venv\Scripts\python.exe", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=r"c:\SmartFit\backend"
)

# Wait up to 10 seconds for server ready
for i in range(10):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as resp:
            data = json.loads(resp.read().decode())
            print(f"Server is ready! Health check: {data}")
            break
    except Exception:
        time.sleep(1)

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/hardware/spec") as resp:
        spec = json.loads(resp.read().decode())
        print("\nHardware Spec:")
        print(" - Knee Band Sensors:", [s["name"] for s in spec["knee_band"]["sensors"]])
        print(" - Chest Belt Sensors:", [s["name"] for s in spec["chest_belt"]["sensors"]])

    with urllib.request.urlopen("http://127.0.0.1:8000/api/patients") as resp:
        patients = json.loads(resp.read().decode())
        print(f"\nPatients found: {len(patients)}")
        for p in patients:
            bmi = p["weight"] / ((p["height"] / 100) ** 2)
            print(f" - {p['patient_id']}: {p['name']}, Age: {p['age']}, BMI: {bmi:.1f}")

    with urllib.request.urlopen("http://127.0.0.1:8000/api/reports/summary/SF-1001") as resp:
        rep = json.loads(resp.read().decode())
        print(f"\nReport Summary for SF-1001:")
        print(f" - OAI Risk Result: {rep['oa_clinical_result']['stage']} ({rep['oa_clinical_result']['probability']}%)")

    print("\nALL FASTAPI BACKEND VERIFICATION CHECKS PASSED PERFECTLY!")

finally:
    proc.terminate()
    proc.wait()
