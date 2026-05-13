"""Data preprocessing: scaling and train/test split."""

import pandas as pd
from sklearn.preprocessing import StandardScaler


def preprocess_data(input_path: str, output_path: str) -> str:
    """Scale features and save the cleaned dataset."""
    df = pd.read_csv(input_path)

    feature_cols = [c for c in df.columns if c != "label"]
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    # Drop rows with any nulls (real pipelines would handle this more carefully)
    df.dropna(inplace=True)

    df.to_csv(output_path, index=False)
    print(f"Preprocessed {len(df)} rows -> {output_path}")
    return output_path
