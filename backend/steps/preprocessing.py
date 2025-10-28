# backend/steps/preprocessing.py

from typing import Tuple
from zenml import step
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

@step
def data_preprocessing_step(
    df: pd.DataFrame, target_col: str = "species", test_size: float = 0.2, random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series]:
    """
    Preprocess the dataframe:
      - drop NA
      - split into X/y
      - scale features
      - train/test split
    Returns: X_train, X_test, y_train, y_test
    """
    print("[2/6] 🧹 Starting data preprocessing...")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame columns: {df.columns.tolist()}")

    df_clean = df.dropna().reset_index(drop=True)
    print(f"[   ] Dropped NA: {len(df) - len(df_clean)} rows removed (if any).")

    X = df_clean.drop(columns=[target_col])
    y = df_clean[target_col]

    if X.shape[1] == 0:
        raise ValueError("No feature columns left after dropping the target column.")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=test_size, random_state=random_state, stratify=y if len(y.unique()) > 1 else None
    )

    print(f"[✔] Data preprocessing completed. Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    return X_train, X_test, y_train, y_test
