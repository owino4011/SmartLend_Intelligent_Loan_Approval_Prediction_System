import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils import ensure_dir, get_logger

logger = get_logger("evaluation", "logs/evaluation_log.log")

def evaluate_and_report(model, X_test, y_test, reports_dir="reports"):
    ensure_dir(reports_dir)
    logger.info("Running predictions for evaluation...")
    preds = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_test)[:, 1]
    else:
        probs = None

    #classification report
    creport = classification_report(y_test, preds, output_dict=True)
    creport_df = pd.DataFrame(creport).transpose()
    creport_df.to_csv(os.path.join(reports_dir, "classification_report.csv"), index=True)
    logger.info("classification_report.csv saved")

    #confusion matrix
    cm = confusion_matrix(y_test, preds)
    cm_df = pd.DataFrame(cm, index=["actual_0", "actual_1"], columns=["pred_0", "pred_1"])
    cm_df.to_csv(os.path.join(reports_dir, "confusion_matrix.csv"), index=True)
    logger.info("confusion_matrix.csv saved")

    #confusion matrix figure
    fig, ax = plt.subplots(figsize=(5,4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    fig.tight_layout()
    fig_path = os.path.join(reports_dir, "confusion_matrix.png")
    fig.savefig(fig_path)
    plt.close(fig)
    logger.info(f"confusion_matrix.png saved to {fig_path}")

    return creport_df, cm_df


