from src.training.trainer import fine_tune_model
import pandas as pd
from src.data_processing.data_cleaner import create_dataset

def main():
    # Load processed data
    df = pd.read_csv("data/processed/cleaned_financial_news.csv")
    dataset = create_dataset(df)
    
    # Fine-tune model
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    output_dir = "models/fine_tuned"
    fine_tune_model(model_name, dataset, output_dir)

if __name__ == "__main__":
    main()
