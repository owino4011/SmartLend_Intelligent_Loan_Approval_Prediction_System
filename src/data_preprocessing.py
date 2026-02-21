import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from src.utils import ensure_dir

NUMERIC_COLS = [
    "person_age", "person_income", "person_emp_exp",
    "loan_amnt", "loan_int_rate", "loan_percent_income",
    "cb_person_cred_hist_length", "credit_score"
]
CATEGORICAL_COLS = [
    "person_gender", "person_education", "person_home_ownership",
    "loan_intent", "previous_loan_defaults_on_file"
]
TARGET = "loan_status"

CAPS = {
    "person_age": 100,
    "person_emp_exp": 50
}

def load_raw(path="data/raw/loan_data.csv"):
    df = pd.read_csv(path)
    return df

def basic_clean_and_cap(df: pd.DataFrame):
    df = df.copy()
    
    for c in NUMERIC_COLS + CATEGORICAL_COLS + [TARGET]:
        if c not in df.columns:
            raise KeyError(f"Expected column '{c}' not found in dataframe")
    # droping NA rows if any
    df = df.dropna(subset=[TARGET])
    for col, cap in CAPS.items():
        if col in df.columns:
            df[col] = np.where(df[col] > cap, cap, df[col])
    return df

def build_preprocessor():
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    transformer = ColumnTransformer([
        ("num", num_pipeline, NUMERIC_COLS),
        ("cat", cat_pipeline, CATEGORICAL_COLS)
    ], remainder="drop")
    return transformer

def preprocess_and_split(save_processed=True, raw_path="data/raw/loan_data.csv", processed_dir="data/processed"):
    ensure_dir(processed_dir)
    df = load_raw(raw_path)
    df = basic_clean_and_cap(df)
    #rain/test split stratify by target
    X = df.drop(columns=[TARGET])
    y = df[TARGET].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    if save_processed:
        train = X_train.copy()
        train[TARGET] = y_train
        test = X_test.copy()
        test[TARGET] = y_test
        train.to_csv(os.path.join(processed_dir, "train.csv"), index=False)
        test.to_csv(os.path.join(processed_dir, "test.csv"), index=False)
    return X_train, X_test, y_train, y_test

