from src.model_training import train_and_save
from src.utils import get_logger
logger = get_logger("pipeline", "logs/pipeline.log")

def run(X_train, y_train):
    logger.info("Step 3: Training model...")
    model = train_and_save(X_train, y_train)
    logger.info("Training script finished.")
    print("Training script finished.")
    return model

if __name__ == "__main__":
    print("This script is intended to be called from main.py")


