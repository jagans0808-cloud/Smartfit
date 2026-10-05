"""
SmartFit - Random Forest Exercise and Movement Classification Model Trainer
Based on Biomedfinix2 SIH26213 Technical Approach:
- Sensor Data -> Signal Processing -> Feature Extraction -> Multimodal Data Fusion -> Random Forest -> Exercise Classification
"""

import os
from pathlib import Path
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODELS_DIR / "exercise_rf_model.joblib"

EXERCISE_CLASSES = [
    "Resting / Standing",
    "Squats",
    "Lunges",
    "Knee Flexion-Extension",
    "Walking / Gait"
]

FEATURE_NAMES = [
    "knee_angle_mean",
    "knee_angle_rom",
    "knee_angle_velocity_max",
    "flex_sensor_mean",
    "heel_pressure_mean",
    "forefoot_pressure_mean",
    "pressure_heel_forefoot_ratio",
    "chest_accel_mag_mean",
    "chest_accel_var",
    "trunk_tilt_angle",
    "heart_rate_bpm",
    "cadence_rpm"
]

def generate_biomechanical_dataset(samples_per_class=400, random_state=42):
    np.random.seed(random_state)
    X = []
    y = []

    for class_idx, class_name in enumerate(EXERCISE_CLASSES):
        for _ in range(samples_per_class):
            if class_idx == 0:  # Resting / Standing
                knee_angle_mean = np.random.normal(172, 3)
                knee_angle_rom = np.random.uniform(2, 10)
                knee_vel_max = np.random.uniform(5, 25)
                flex_mean = np.random.normal(15, 5)
                heel_p = np.random.normal(55, 6)
                forefoot_p = np.random.normal(45, 6)
                chest_mag = np.random.normal(9.81, 0.15)
                chest_var = np.random.uniform(0.01, 0.2)
                trunk_tilt = np.random.normal(4, 2)
                hr = np.random.normal(72, 6)
                cadence = 0.0

            elif class_idx == 1:  # Squats
                knee_angle_mean = np.random.normal(110, 8)
                knee_angle_rom = np.random.normal(82, 6)
                knee_vel_max = np.random.normal(140, 20)
                flex_mean = np.random.normal(78, 8)
                heel_p = np.random.normal(68, 8)
                forefoot_p = np.random.normal(65, 8)
                chest_mag = np.random.normal(10.2, 0.8)
                chest_var = np.random.uniform(1.2, 3.5)
                trunk_tilt = np.random.normal(32, 5)
                hr = np.random.normal(122, 12)
                cadence = np.random.uniform(15, 25)

            elif class_idx == 2:  # Lunges
                knee_angle_mean = np.random.normal(118, 9)
                knee_angle_rom = np.random.normal(74, 7)
                knee_vel_max = np.random.normal(125, 18)
                flex_mean = np.random.normal(68, 7)
                heel_p = np.random.normal(42, 8)
                forefoot_p = np.random.normal(78, 8)
                chest_mag = np.random.normal(10.0, 0.7)
                chest_var = np.random.uniform(1.0, 2.8)
                trunk_tilt = np.random.normal(18, 4)
                hr = np.random.normal(128, 14)
                cadence = np.random.uniform(14, 22)

            elif class_idx == 3:  # Knee Flexion-Extension (seated/isolated)
                knee_angle_mean = np.random.normal(135, 7)
                knee_angle_rom = np.random.normal(65, 6)
                knee_vel_max = np.random.normal(110, 15)
                flex_mean = np.random.normal(62, 6)
                heel_p = np.random.normal(12, 5)
                forefoot_p = np.random.normal(10, 4)
                chest_mag = np.random.normal(9.82, 0.2)
                chest_var = np.random.uniform(0.05, 0.4)
                trunk_tilt = np.random.normal(6, 3)
                hr = np.random.normal(95, 8)
                cadence = np.random.uniform(16, 26)

            elif class_idx == 4:  # Walking / Gait
                knee_angle_mean = np.random.normal(155, 5)
                knee_angle_rom = np.random.normal(52, 5)
                knee_vel_max = np.random.normal(210, 25)
                flex_mean = np.random.normal(42, 6)
                heel_p = np.random.normal(70, 10)
                forefoot_p = np.random.normal(75, 10)
                chest_mag = np.random.normal(11.1, 1.2)
                chest_var = np.random.uniform(2.5, 5.0)
                trunk_tilt = np.random.normal(8, 3)
                hr = np.random.normal(108, 10)
                cadence = np.random.uniform(50, 68)

            ratio = heel_p / (forefoot_p + 1e-4)

            feat = [
                knee_angle_mean,
                knee_angle_rom,
                knee_vel_max,
                flex_mean,
                heel_p,
                forefoot_p,
                ratio,
                chest_mag,
                chest_var,
                trunk_tilt,
                hr,
                cadence
            ]
            X.append(feat)
            y.append(class_idx)

    return np.array(X), np.array(y)

def train_and_export():
    print("Generating biomechanical training dataset for Random Forest classifier...")
    X, y = generate_biomechanical_dataset(samples_per_class=500, random_state=42)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples")

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=120,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Training Completed! Validation Accuracy: {acc * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, target_names=EXERCISE_CLASSES))

    model_bundle = {
        "pipeline": pipeline,
        "classes": EXERCISE_CLASSES,
        "features": FEATURE_NAMES,
        "model_version": "SmartFit-RF-v1.0",
        "algorithm": "Random Forest Classifier (Scikit-Learn)",
        "framework": "Python + Scikit-Learn",
        "description": "Multimodal movement & exercise classifier based on knee kinematics, plantar pressure, and chest IMU/HR dynamics.",
        "disclaimer": "This AI model provides exercise and movement classification for fitness tracking and rehabilitation research. It is not an OA diagnostic classifier."
    }

    joblib.dump(model_bundle, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_and_export()
