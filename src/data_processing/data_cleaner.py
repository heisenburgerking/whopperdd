import pandas as pd
import re
from datasets import Dataset

def clean_korean_text(text):
    return re.sub(r"[^가-힣\s.,!?0-9]", "", text)

def clean_data(input_file, output_file):
    df = pd.read_csv(input_file)
    
    df['text_content'] = df['text_content'].apply(clean_korean_text)
    df = df[df['text_content'].str.len() >= 100]
    df = df.drop_duplicates().dropna()
    
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")
    
    return df

def create_dataset(df):
    return Dataset.from_pandas(df)

if __name__ == "__main__":
    input_file = "data/raw/financial_news_full.csv"
    output_file = "data/processed/cleaned_financial_news.csv"
    df = clean_data(input_file, output_file)
    dataset = create_dataset(df)
    print("Dataset created successfully")
