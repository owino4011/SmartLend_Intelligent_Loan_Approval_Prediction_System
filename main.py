"""
Run the whole pipeline end-to-end with detailed messages
"""

from scripts.data_ingestion import run as ingest
from scripts.split_data import run as split_run
from scripts.train_model import run as train_run
from scripts.evaluate_model import run as eval_run
from src.utils import get_logger, ensure_dir
import joblib
import os

logger = get_logger("main", "logs/pipeline.log")

def main():
    print("\n== SmartLend Loan Approval ML Pipeline ==\n")
    logger.info("Pipeline started")

    # 1.Data Ingestion
    print("Step 1: Data Ingestion...")
    df = ingest()
    print("Data Ingestion completed. Shape:", df.shape)
    logger.info("Data ingestion completed. Shape: %s", df.shape)

    # 2.Data Preprocessing & Split
    print("\nStep 2: Data Preprocessing & Split...")
    X_train, X_test, y_train, y_test = split_run()
    print(f"Data Preprocessing completed. Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    logger.info("Data preprocessing and split completed. Train shape: %s, Test shape: %s", X_train.shape, X_test.shape)

    # 3.Model Training
    print("\nStep 3: Model Training...")
    from src.model_training import train_and_save

    #passing X_test and y_test
    model = train_and_save(X_train, y_train, X_test, y_test, model_path="models/loan_approval_model.pkl")

    print("Model training completed. Model saved to models/loan_approval_model.pkl")
    logger.info("Model training completed and saved to models/loan_approval_model.pkl")

    # 4.Model Evaluation
    print("\nStep 4: Model Evaluation...")
    from src.model_evaluation import evaluate_and_report
    evaluate_and_report(model, X_test, y_test)
    print("Model evaluation completed. Reports saved to /reports")
    logger.info("Model evaluation completed. Reports saved to /reports")

    #Completion
    print("\n== ML Pipeline completed successfully! ==")
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    #Ensuring necessary directories exist
    ensure_dir("models")
    ensure_dir("reports")
    ensure_dir("logs")
    main()



