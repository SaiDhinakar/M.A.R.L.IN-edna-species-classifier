# backend/steps/ingestion.py

from typing import Optional
import pandas as pd
from zenml import step

@step
def data_ingestion_step(file_path: str = "../data/sample.csv") -> pd.DataFrame:
    """Read CSV from disk and return a DataFrame."""
    print("[1/6] 🚀 Starting data ingestion...")
    try:
        df = pd.read_csv(file_path)
        print(f"[✔] Data ingestion completed. Loaded {len(df)} records from '{file_path}'.")
        return df
    except FileNotFoundError as exc:
        print(f"[❌] Data file not found at: {file_path}")
        raise exc

if __name__ == '__main__':
    print(data_ingestion_step())