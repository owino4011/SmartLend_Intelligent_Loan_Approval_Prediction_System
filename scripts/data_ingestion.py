from src.data_preprocessing import load_raw
from src.utils import get_logger
logger = get_logger("pipeline", "logs/pipeline.log")

def run():
    logger.info("Step 1: Data Ingestion - Loading raw CSV...")
    df = load_raw()
    logger.info(f"Data loaded with shape {df.shape}")
    print("Data ingestion complete.")
    return df

if __name__ == "__main__":
    run()


