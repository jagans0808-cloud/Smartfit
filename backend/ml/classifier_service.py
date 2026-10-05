"""
SmartFit - AI Inference Engine
Combines:
1. Random Forest Classifier (Exercise / Movement Classification & Performance Output)
2. NIH OAI Clinical Reference Classifier (Radiographic Osteoarthritis Risk Screening)
"""

from pathlib import Path
from typing import Dict, Any, List
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
EXERCISE_MODEL_PATH = MODELS_DIR / "exercise_rf_model.joblib"
OA_MODEL_PATH = MODELS_DIR / "oa_model.joblib"

class AIService:
    def __init__(self):
        self.rf_bundle = None
        self.oa_model = None
        self._load_models()

    def _load_models(self):
        if EXERCISE_MODEL_PATH.exists():
            try:
                self.rf_bundle = joblib.load(EXERCISE_MODEL_PATH)
                print("Loaded Random Forest Exercise Classifier successfully.")
            except Exception as e:
                print(f"Error loading RF model: {e}")

        if OA_MODEL_PATH.exists():
            try:
                self.oa_model = joblib.load(OA_MODEL_PATH)
                print("Loaded OA Clinical Reference Model successfully.")
            except Exception as e:
                print(f"Error loading OA model: {e}")

    def classify_exercise(self, feature_vector: List[float]) -> Dict[str, Any]:
        """
        Runs Random Forest model for Exercise / Movement classification.
        Output: Exercise class, confidence probabilities, feature importance, status.
        """
        if not self.rf_bundle:
            self._load_models()

        if not self.rf_bundle:
            return {
                "error": "Random Forest model not loaded",
                "exercise_name": "Unknown",
                "confidence": 0.0,
                "probabilities": {}
            }

        pipeline = self.rf_bundle["pipeline"]
        classes = self.rf_bundle["classes"]
        feature_names = self.rf_bundle["features"]

        arr = np.array([feature_vector], dtype=float)
        probas = pipeline.predict_proba(arr)[0]
        best_idx = int(np.argmax(probas))
        best_class = classes[best_idx]
        confidence = round(float(probas[best_idx]) * 100, 1)

        prob_dict = {classes[i]: round(float(probas[i]) * 100, 1) for i in range(len(classes))}

        return {
            "exercise_name": best_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "model_version": self.rf_bundle.get("model_version", "SmartFit-RF-v1.0"),
            "algorithm": "Random Forest (Scikit-Learn)",
            "disclaimer": "AI-assisted movement classification research prototype. Not a medical diagnostic model."
        }

    def compute_oa_clinical_risk(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the NIH OAI Clinical Reference Classifier from the existing OA system.
        Predicts epidemiological radiographic OA risk based on Age, BMI, and Symptom presence.
        """
        if not self.oa_model:
            self._load_models()

        if not self.oa_model:
            return {
                "error": "OA Clinical Model not initialized",
                "probability": 0.0,
                "stage": "Model Unavailable"
            }

        height_m = (patient.get("height", 170.0) / 100.0)
        weight_kg = patient.get("weight", 70.0)
        bmi = weight_kg / (height_m ** 2) if height_m > 0 else 24.0

        m = self.oa_model
        pipeline = m["pipeline"] if isinstance(m, dict) and "pipeline" in m else m
        model_version = m.get("model_version", "OAI-LogReg-v2.1") if isinstance(m, dict) else "OAI-LogReg-v2.1"

        model_bmi = bmi
        if hasattr(pipeline, "named_steps") and "scale" in pipeline.named_steps:
            scaler_mean_bmi = float(pipeline.named_steps["scale"].mean_[1])
            if scaler_mean_bmi < 1.0 and bmi > 5.0:
                model_bmi = bmi / 100.0

        has_pain = 1 if (patient.get("pain_side") and patient["pain_side"] not in ("None", "none", "")) else 0
        clinical_features = np.array([[patient.get("age", 45), model_bmi, has_pain]], dtype=float)

        try:
            prob = float(pipeline.predict_proba(clinical_features)[0, 1])
        except Exception as ex:
            return {"error": f"OA model inference failed: {str(ex)}"}

        prob_pct = round(prob * 100, 1)

        if prob < 0.33:
            stage = "Lower Epidemiological OA Likelihood"
        elif prob < 0.66:
            stage = "Intermediate Epidemiological OA Likelihood"
        else:
            stage = "Higher Epidemiological OA Likelihood"

        suggestions = {
            "Lower Epidemiological OA Likelihood": [
                "Maintain regular low-impact aerobic physical activity and functional movement.",
                "Continue joint-sparing functional mobility and healthy weight habits.",
                "Schedule clinical consultation if localized joint pain, morning stiffness, or swelling arises."
            ],
            "Intermediate Epidemiological OA Likelihood": [
                "Discuss persistent knee symptoms with a primary healthcare clinician or physiotherapist.",
                "Engage in supervised quadriceps and hamstring strengthening to support joint alignment.",
                "Repeat biomechanical screening in 6 months to monitor functional kinematic stability."
            ],
            "Higher Epidemiological OA Likelihood": [
                "Arrange formal orthopedic evaluation and clinical examination for treatment planning.",
                "Consider weight-bearing bilateral knee radiographs to inspect anatomical joint space.",
                "Engage in low-impact or aquatic exercise; avoid repetitive high-impact loaded flexion."
            ]
        }[stage]

        return {
            "probability": prob_pct,
            "stage": stage,
            "model_name": "NIH Osteoarthritis Initiative (OAI) Clinical Reference Model",
            "model_version": model_version,
            "ground_truth": "Radiographic knee OA presence at baseline (Kellgren-Lawrence Grade >= 2)",
            "predictors": {
                "age": patient.get("age", 45),
                "bmi": round(bmi, 1),
                "symptom_presence": has_pain
            },
            "suggestions": suggestions,
            "disclaimer": "The OAI model assesses epidemiological radiographic risk from clinical parameters. Wearable sensor features represent dynamic functional kinematics and are documented separately as dynamic mobility indicators."
        }

ai_service = AIService()
