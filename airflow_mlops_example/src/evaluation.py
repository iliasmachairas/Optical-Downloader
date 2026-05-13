"""Model evaluation: compute and persist key metrics."""

import json
import pickle

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


def evaluate_model(data_path: str, model_path: str, metrics_path: str) -> dict:
    """Evaluate the trained model and write metrics to a JSON file."""
    df = pd.read_csv(data_path)
    X = df.drop(columns=["label"])
    y = df["label"]

    # Use the same split as training so we evaluate on the held-out set
    _X_train, X_test, _y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Evaluation metrics: {metrics}")
    print(f"Metrics saved -> {metrics_path}")
    return metrics
