"""Simulate data ingestion from a source (e.g. database, API, S3)."""

import pandas as pd
import numpy as np


def ingest_data(output_path: str) -> str:
    """Generate a synthetic dataset and save it to disk."""
    rng = np.random.default_rng(seed=42)
    n = 1000

    df = pd.DataFrame(
        {
            "feature_1": rng.normal(0, 1, n),
            "feature_2": rng.normal(5, 2, n),
            "feature_3": rng.uniform(0, 10, n),
            "label": rng.integers(0, 2, n),  # binary classification
        }
    )

    df.to_csv(output_path, index=False)
    print(f"Ingested {len(df)} rows -> {output_path}")
    return output_path
