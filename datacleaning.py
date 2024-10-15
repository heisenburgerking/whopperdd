import os
import time
import pandas as pd
import re
from datasets import load_dataset, Dataset
from litellm import batch_completion, RateLimitError, AuthenticationError

# Ensure output directory exists
output_dir = "output_path"
os.makedirs(output_dir, exist_ok=True)

# Load dataset
print("Loading dataset...")
ds = load_dataset('landaucs/krx1')['train']
texts = [bt for bt in ds['text_content'] for _ in range(2)]

# Clean text: Remove non-Korean characters (optional)
def clean_korean_text(text):
    return re.sub(r"[^가-힣\s.,!?0-9]", "", text)

texts = [clean_korean_text(t) for t in texts]

# Filter out texts that are too short
texts = [t for t in texts if len(t) >= 100]

# Generate prompts
qrys = [
    [
        {"role": "system", "content": "Your job is creating multi-hop reasoning questions in fluent Korean. "
                                      "You will be given a part of a text. Make a question based on it. "
                                      "The question should require multiple steps of reasoning related to the text. "
                                      "Return the question only without any other text."},
        {"role": "user", "content": t}
    ] for t in texts
]

# Retry logic with exponential backoff
def process_batches(qrys, model_name, max_attempts=5):
    responses = []
    for i in range(0, len(qrys), 5):
        batch = qrys[i:i + 5]
        success = False
        attempt = 0

        while not success and attempt < max_attempts:
            try:
                response = batch_completion(model=model_name, messages=batch)
                responses.extend(response)
                success = True
            except RateLimitError:
                attempt += 1
                print(f"Rate limit hit. Retrying in {5 ** attempt} seconds...")
                time.sleep(min(5 ** attempt, 300))
            except AuthenticationError as e:
                print(f"Authentication failed: {e}")
                return []
            except Exception as e:
                print(f"Error: {e}")
                break
    return responses

# Process batches and generate questions
print("Generating questions...")
responses = process_batches(qrys, "gpt-4o-mini-2024-07-18")
resps = [r.choices[0].message.content if hasattr(r, 'choices') else "Error" for r in responses]

# Create DataFrame
df = pd.DataFrame({'sampled_text': texts, 'question': resps})

# Data Cleaning: Remove duplicates and handle missing values
df = df.drop_duplicates().dropna()
df['sampled_text'] = df['sampled_text'].astype(str).str.strip()
df['question'] = df['question'].astype(str).str.strip()

# Check if DataFrame is empty
if df.empty:
    print("Warning: The DataFrame is empty after cleaning.")
else:
    # Save cleaned data to CSV and Excel
    df.to_csv(os.path.join(output_dir, "cleaned_result.csv"), index=False)
    df.to_excel(os.path.join(output_dir, "cleaned_result.xlsx"), index=False)

    print("Cleaned data saved successfully.")
    print(df.head())  # Preview top 5 rows

# Optional: Upload to Hugging Face Hub
try:
    from huggingface_hub import login
    login(token="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")
    result_df = Dataset.from_pandas(df)
    result_df.push_to_hub("landaucs/krx1", token="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")
    print("Data uploaded to Hugging Face Hub.")
except ImportError:
    print("huggingface_hub not installed. Skipping upload.")
except Exception as e:
    print(f"Error uploading to Hugging Face: {e}")
