from src.data_processing.data_cleaner import clean_data, create_dataset
import pandas as pd

def main():
    # Step 1: Clean data
    input_file = "data/raw/financial_news_full.csv"
    output_file = "data/processed/cleaned_financial_news.csv"
    df = clean_data(input_file, output_file)
    
    # Step 2: Create dataset
    dataset = create_dataset(df)
    print("Dataset created successfully")

if __name__ == "__main__":
    main()
