"""Model training using a Random Forest classifier."""

import json
import pickle

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def train_model(data_path: str, model_path: str) -> str:
    """Train a Random Forest and persist it to disk."""
    df = pd.read_csv(data_path)

    X = df.drop(columns=["label"])
    y = df["label"]

    X_train, _X_val, y_train, _y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"Model trained and saved -> {model_path}")
    return model_path
