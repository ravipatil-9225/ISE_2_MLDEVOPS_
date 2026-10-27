"""
app/model.py - Model loader for the Iris prediction service.

Loads the pre-trained model.pkl once at startup and exposes a
`predict(features)` helper that returns the class name as a string.
"""

import os
import joblib
import numpy as np

# Resolve the model path relative to this file's location,
# so it works whether started from the repo root or the app/ directory.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(_BASE_DIR, "model.pkl")

# ── Module-level state (loaded once) ──────────────────────────────────────────
_model = None
_class_names = None


def load_model(path: str = MODEL_PATH) -> None:
    """
    Load the trained model from disk into module-level variables.
    Called once during application startup.
    """
    global _model, _class_names
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"model.pkl not found at {path}. "
            "Run `python train.py` first."
        )
    payload = joblib.load(path)
    _model = payload["model"]
    _class_names = payload["class_names"]
    print(f"[model] Loaded from {path}. Classes: {_class_names}")


def predict(features: list) -> dict:
    """
    Run inference on a list of 4 numeric features.

    Args:
        features: [sepal_length, sepal_width, petal_length, petal_width]

    Returns:
        dict with 'class_name' (str) and 'class_index' (int).

    Raises:
        ValueError: if features list is not exactly length 4.
        RuntimeError: if the model has not been loaded yet.
    """
    if _model is None or _class_names is None:
        raise RuntimeError("Model is not loaded. Call load_model() first.")

    if len(features) != 4:
        raise ValueError(
            f"Expected 4 features, got {len(features)}."
        )

    arr = np.array(features, dtype=float).reshape(1, -1)
    class_index = int(_model.predict(arr)[0])
    class_name = _class_names[class_index]

    return {"class_name": class_name, "class_index": class_index}
