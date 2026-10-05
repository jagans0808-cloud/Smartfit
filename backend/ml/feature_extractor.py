"""
SmartFit - Multimodal Feature Extraction & Signal Processing Pipeline
Follows Biomedfinix2 System Architecture:
Sensor Data -> Signal Processing -> Feature Extraction -> Multimodal Data Fusion -> Random Forest Classifier
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np

def compute_knee_angle(thigh_pitch: float, shin_pitch: float, flex_deg: Optional[float] = None) -> float:
    """
    Computes anatomical knee joint angle from dual MPU6050 IMUs + Flex Sensor fusion.
    Full standing extension is ~170-180 deg; 90 deg flexion is right angle; deep squat is 70-110 deg.
    """
    imu_angle = 180.0 - abs(thigh_pitch - shin_pitch)
    if flex_deg is not None:
        # Complementary fusion between IMU angle and Flex sensor bend
        fused = 0.7 * imu_angle + 0.3 * (180.0 - flex_deg)
        return round(float(np.clip(fused, 40.0, 180.0)), 1)
    return round(float(np.clip(imu_angle, 40.0, 180.0)), 1)

def extract_features_from_buffer(
    knee_buffer: List[Dict[str, Any]],
    chest_buffer: List[Dict[str, Any]],
    default_hr: float = 75.0
) -> Dict[str, Any]:
    """
    Extracts time-domain, frequency, and kinematic features from sliding telemetry buffers.
    Buffers contain time-aligned samples from Knee Band and Chest Belt.
    """
    # 1. Process Knee Band parameters
    if knee_buffer:
        angles = [s.get("knee_angle", 175.0) for s in knee_buffer]
        flex_vals = [s.get("flex_sensor", 15.0) for s in knee_buffer]
        heel_vals = [s.get("heel_pressure", 50.0) for s in knee_buffer]
        forefoot_vals = [s.get("forefoot_pressure", 45.0) for s in knee_buffer]

        knee_angle_mean = float(np.mean(angles))
        knee_angle_rom = float(np.max(angles) - np.min(angles))

        # Peak angular velocity approximation
        diffs = np.diff(angles)
        knee_angle_velocity_max = float(np.max(np.abs(diffs))) * 25.0 if len(diffs) > 0 else 10.0

        flex_sensor_mean = float(np.mean(flex_vals))
        heel_pressure_mean = float(np.mean(heel_vals))
        forefoot_pressure_mean = float(np.mean(forefoot_vals))
        ratio = heel_pressure_mean / (forefoot_pressure_mean + 1e-4)
    else:
        knee_angle_mean = 175.0
        knee_angle_rom = 5.0
        knee_angle_velocity_max = 5.0
        flex_sensor_mean = 15.0
        heel_pressure_mean = 50.0
        forefoot_pressure_mean = 45.0
        ratio = 1.11

    # 2. Process Chest Belt parameters
    if chest_buffer:
        chest_accels = []
        tilts = []
        hrs = []
        for s in chest_buffer:
            ax = s.get("accel_x", 0.0)
            ay = s.get("accel_y", 0.0)
            az = s.get("accel_z", 9.81)
            mag = math.sqrt(ax * ax + ay * ay + az * az)
            chest_accels.append(mag)

            # Trunk tilt relative to gravity vector
            tilt = math.degrees(math.atan2(math.sqrt(ax * ax + ay * ay), abs(az) + 1e-5))
            tilts.append(tilt)

            if "heart_rate" in s and s["heart_rate"] is not None and s["heart_rate"] > 30:
                hrs.append(s["heart_rate"])

        chest_accel_mag_mean = float(np.mean(chest_accels)) if chest_accels else 9.81
        chest_accel_var = float(np.var(chest_accels)) if chest_accels else 0.05
        trunk_tilt_angle = float(np.mean(tilts)) if tilts else 5.0
        heart_rate_bpm = float(np.mean(hrs)) if hrs else default_hr
    else:
        chest_accel_mag_mean = 9.81
        chest_accel_var = 0.05
        trunk_tilt_angle = 5.0
        heart_rate_bpm = default_hr

    # Repetition estimation and Cadence (RPM)
    rep_count = count_repetitions(knee_buffer)
    duration_s = max(len(knee_buffer), len(chest_buffer)) * 0.04  # Assuming ~25Hz sample rate
    cadence_rpm = round((rep_count / (duration_s / 60.0)), 1) if duration_s > 5 and rep_count > 0 else 0.0

    feature_dict = {
        "knee_angle_mean": round(knee_angle_mean, 2),
        "knee_angle_rom": round(knee_angle_rom, 2),
        "knee_angle_velocity_max": round(knee_angle_velocity_max, 2),
        "flex_sensor_mean": round(flex_sensor_mean, 2),
        "heel_pressure_mean": round(heel_pressure_mean, 2),
        "forefoot_pressure_mean": round(forefoot_pressure_mean, 2),
        "pressure_heel_forefoot_ratio": round(ratio, 2),
        "chest_accel_mag_mean": round(chest_accel_mag_mean, 2),
        "chest_accel_var": round(chest_accel_var, 3),
        "trunk_tilt_angle": round(trunk_tilt_angle, 2),
        "heart_rate_bpm": round(heart_rate_bpm, 1),
        "cadence_rpm": round(cadence_rpm, 1),
        "rep_count": rep_count
    }

    feature_vector = [
        feature_dict["knee_angle_mean"],
        feature_dict["knee_angle_rom"],
        feature_dict["knee_angle_velocity_max"],
        feature_dict["flex_sensor_mean"],
        feature_dict["heel_pressure_mean"],
        feature_dict["forefoot_pressure_mean"],
        feature_dict["pressure_heel_forefoot_ratio"],
        feature_dict["chest_accel_mag_mean"],
        feature_dict["chest_accel_var"],
        feature_dict["trunk_tilt_angle"],
        feature_dict["heart_rate_bpm"],
        feature_dict["cadence_rpm"]
    ]

    return {
        "features": feature_dict,
        "vector": feature_vector,
        "rep_count": rep_count
    }

def count_repetitions(knee_buffer: List[Dict[str, Any]], threshold_rom: float = 35.0) -> int:
    """
    Peak-valley detection with hysteresis on knee angle curve.
    """
    if len(knee_buffer) < 15:
        return 0

    angles = [s.get("knee_angle", 175.0) for s in knee_buffer]
    reps = 0
    state = "EXTENDED"  # EXTENDED or FLEXED
    flex_threshold = 135.0
    extend_threshold = 160.0

    for a in angles:
        if state == "EXTENDED" and a < flex_threshold:
            state = "FLEXED"
        elif state == "FLEXED" and a > extend_threshold:
            reps += 1
            state = "EXTENDED"

    return reps

def assess_movement_form(features: Dict[str, Any], exercise_name: str) -> Dict[str, Any]:
    """
    Evaluates execution form, safety margins, and triggers vibration alerts for deviations.
    """
    score = 85.0
    warnings = []
    vibration_alert = False
    vibration_reason = None

    trunk_tilt = features.get("trunk_tilt_angle", 5.0)
    knee_rom = features.get("knee_angle_rom", 0.0)
    ratio = features.get("pressure_heel_forefoot_ratio", 1.0)

    if exercise_name == "Squats":
        if trunk_tilt > 45.0:
            score -= 20.0
            warnings.append("Excessive forward trunk lean detected.")
            vibration_alert = True
            vibration_reason = "Excessive trunk flexion during squat"
        if knee_rom < 60.0 and features.get("rep_count", 0) > 0:
            score -= 15.0
            warnings.append("Sub-optimal depth; knee flexion range under 60°.")
        if ratio < 0.5:
            score -= 10.0
            warnings.append("Heel lift detected; weight shifting too far forward onto forefoot.")
            vibration_alert = True
            vibration_reason = "Plantar imbalance: Heel lifting off floor"

    elif exercise_name == "Lunges":
        if trunk_tilt > 30.0:
            score -= 15.0
            warnings.append("Trunk tilting off vertical axis.")
        if knee_rom < 50.0:
            score -= 15.0
            warnings.append("Lunge knee flexion shallow.")

    score = max(30.0, min(100.0, score))

    status = "Optimal Form" if score >= 80 else ("Acceptable Form" if score >= 65 else "Needs Form Correction")

    return {
        "form_score": round(score, 1),
        "status": status,
        "warnings": warnings,
        "vibration_alert": vibration_alert,
        "vibration_reason": vibration_reason
    }
