import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from xgboost import XGBClassifier 
from src.data_preprocessing import build_preprocessor, NUMERIC_COLS, CATEGORICAL_COLS
from src.utils import ensure_dir, get_logger

logger = get_logger("training", "logs/training_log.log")


def train_and_save(X_train, y_train, X_test, y_test, model_path="models/loan_approval_model.pkl"):
    ensure_dir(os.path.dirname(model_path) or ".")
    preprocessor = build_preprocessor()

    #Oversampling inside the pipeline
    over = RandomOverSampler(random_state=42)

    #Model 1: RandomForest
    rf_clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        class_weight=None
    )

    rf_pipe = ImbPipeline(steps=[
        ("oversample", over),
        ("preprocessor", preprocessor),
        ("clf", rf_clf)
    ])

    logger.info("Training RandomForest...")
    rf_pipe.fit(X_train, y_train)

    #Train accuracy
    rf_pred_train = rf_pipe.predict(X_train)
    rf_acc_train = accuracy_score(y_train, rf_pred_train)
    logger.info(f"RandomForest Training Accuracy: {rf_acc_train:.5f}")

    #Test accuracy
    rf_pred_test = rf_pipe.predict(X_test)
    rf_acc_test = accuracy_score(y_test, rf_pred_test)
    logger.info(f"RandomForest Test Accuracy: {rf_acc_test:.5f}")
    # Model 2: XGBoost
    xgb_clf = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )

    xgb_pipe = ImbPipeline(steps=[
        ("oversample", over),
        ("preprocessor", preprocessor),
        ("clf", xgb_clf)
    ])

    logger.info("Training XGBoost...")
    xgb_pipe.fit(X_train, y_train)

    #Train accuracy
    xgb_pred_train = xgb_pipe.predict(X_train)
    xgb_acc_train = accuracy_score(y_train, xgb_pred_train)
    logger.info(f"XGBoost Training Accuracy: {xgb_acc_train:.5f}")

    #Test accuracy
    xgb_pred_test = xgb_pipe.predict(X_test)
    xgb_acc_test = accuracy_score(y_test, xgb_pred_test)
    logger.info(f"XGBoost Test Accuracy: {xgb_acc_test:.5f}")

    #Comparing the performance and choosing the best model
    if xgb_acc_test > rf_acc_test:
        bestpipe = xgb_pipe
        best_acc = xgb_acc_test
        best_name = "XGBoostClassifier"
    else:
        bestpipe = rf_pipe
        best_acc = rf_acc_test
        best_name = "RandomForestClassifier"

    logger.info(f"Best model selected: {best_name} (Test Accuracy = {best_acc:.5f})")
    logger.info("Saving best model...")

    joblib.dump(bestpipe, model_path)
    logger.info(f"Model saved to {model_path}")

    return bestpipe



