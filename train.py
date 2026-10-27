"""
train.py - Train a Random Forest classifier on the Iris dataset.

This script trains a simple model and saves it as 'model.pkl'.
It is intended to be run once before starting the Flask application,
or as part of the CI/CD pipeline's 'Train Model' stage.
"""

import os
import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_ESTIMATORS = 100


def train_and_save(model_path: str = MODEL_PATH) -> dict:
    """
    Load Iris data, train a Random Forest, evaluate it, and persist the model.

    Returns:
        dict with accuracy and a classification report string.
    """
    print("Loading Iris dataset …")
    iris = load_iris()
    X, y = iris.data, iris.target
    class_names = list(iris.target_names)

    # Split into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"Training RandomForestClassifier (n_estimators={N_ESTIMATORS}) …")
    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=class_names)

    print(f"\nTest Accuracy : {acc:.4f}")
    print("\nClassification Report:")
    print(report)

    # Persist model alongside class names for inference
    payload = {"model": model, "class_names": class_names}
    joblib.dump(payload, model_path)
    print(f"\nModel saved to: {model_path}")

    return {"accuracy": acc, "report": report}


if __name__ == "__main__":
    result = train_and_save()
    print(f"\nDone. Accuracy = {result['accuracy']:.4f}")
