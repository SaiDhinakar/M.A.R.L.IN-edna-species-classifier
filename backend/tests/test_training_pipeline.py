# Training Pipeline will be tested by this file

import sys
sys.path.append(".")  # To ensure backend module is found
from pipelines.training_pipeline import training_pipeline

if __name__ == "__main__":
    # Execute the training pipeline to ensure it runs without errors
    training_pipeline()