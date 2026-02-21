from src.model_evaluation import evaluate_and_report
from src.utils import get_logger
logger = get_logger("pipeline", "logs/pipeline.log")

def run(model, X_test, y_test):
    logger.info("Step 4: Evaluating model...")
    creport_df, cm_df = evaluate_and_report(model, X_test, y_test)
    logger.info("Evaluation finished.")
    print("Evaluation finished.")
    return creport_df, cm_df

if __name__ == "__main__":
    print("This script is intended to be called from main.py")


