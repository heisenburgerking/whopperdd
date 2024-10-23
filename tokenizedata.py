import json
from transformers import AutoTokenizer

# Use AutoTokenizer to load the appropriate tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", use_fast=True)

# 패딩 토큰 설정
tokenizer.pad_token = tokenizer.eos_token  # 또는 tokenizer.add_special_tokens({'pad_token': '[PAD]'}) 사용 가능

print("Tokenizer loaded successfully!")



# Load the prepared training data from JSON
with open("training_data.json", "r") as f:
    training_data = json.load(f)

# Tokenize the data
def tokenize_data(data):
    tokenized_data = []

    for entry in data:
        inputs = tokenizer(
            entry["input"], truncation=True, padding="max_length", max_length=512, return_tensors="pt"
        )
        labels = tokenizer(
            entry["target"], truncation=True, padding="max_length", max_length=512
        )["input_ids"]

        tokenized_data.append({
            "input_ids": inputs["input_ids"].squeeze(0),
            "attention_mask": inputs["attention_mask"].squeeze(0),
            "labels": labels
        })

    return tokenized_data

# Tokenize the loaded training data
tokenized_data = tokenize_data(training_data)
print("Data tokenized successfully!")
