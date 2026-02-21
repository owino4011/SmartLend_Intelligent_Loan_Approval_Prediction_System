from src.data_preprocessing import preprocess_and_split
from src.utils import get_logger
logger = get_logger("pipeline", "logs/pipeline.log")

def run():
    logger.info("Step 2: Data Preprocessing - Cleaning & splitting data...")
    X_train, X_test, y_train, y_test = preprocess_and_split()
    logger.info("Data preprocessing complete.")
    print("Data preprocessing complete.")
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    run()
