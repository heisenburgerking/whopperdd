import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    LlamaForCausalLM,
    Trainer,
    TrainingArguments,
    pipeline
)
from peft import LoraConfig, get_peft_model

# Step 1: Load the Tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", use_fast=True)

# Ensure the tokenizer has a pad token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Step 2: Load the Training Data
print("Loading training data...")
with open("training_data.json", "r") as f:
    training_data = json.load(f)

# Step 3: Tokenize the Data
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

print("Tokenizing data...")
tokenized_data = tokenize_data(training_data)

# Step 4: Create a Dataset and DataLoader
class FinancialDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return {
            "input_ids": self.data[idx]["input_ids"],
            "attention_mask": self.data[idx]["attention_mask"],
            "labels": self.data[idx]["labels"],
        }

print("Creating DataLoader...")
dataset = FinancialDataset(tokenized_data)
dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

# Step 5: Load the LLaMA Model (CPU-Compatible)
print("Loading LLaMA model...")
model = LlamaForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct", 
    device_map="cpu"
)

# Step 6: Apply LoRA for Parameter-Efficient Fine-Tuning
lora_config = LoraConfig(
    r=8,  # Low-rank dimension
    lora_alpha=32,  # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Fine-tune only certain layers
    lora_dropout=0.1,  # Dropout to avoid overfitting
    bias="none",  # No bias fine-tuning
)
model = get_peft_model(model, lora_config)

# Step 7: Define Training Arguments
print("Setting up training arguments...")
training_args = TrainingArguments(
    output_dir="./llama3-mcqa-lora",   # Save directory
    evaluation_strategy="epoch",  # Evaluate at the end of each epoch
    per_device_train_batch_size=1,  # Small batch size for CPU
    gradient_accumulation_steps=8,  # Simulate larger batch size
    num_train_epochs=3,  # Number of epochs
    learning_rate=5e-5,  # Learning rate for fine-tuning
    logging_dir="./logs",  # Log directory for TensorBoard
    save_steps=500,  # Save checkpoint every 500 steps
    save_total_limit=2,  # Keep only the latest 2 checkpoints
    fp16=False,  # Disable mixed precision for CPU
)

# Step 8: Initialize the Trainer and Train the Model
print("Initializing Trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print("Starting training...")
trainer.train()

# Step 9: Save the Fine-Tuned Model and Tokenizer
print("Saving fine-tuned model...")
model.save_pretrained("./llama3-mcqa-lora")
tokenizer.save_pretrained("./llama3-mcqa-lora")

print("Model saved successfully!")

# Step 10: Perform Inference with the Fine-Tuned Model
print("Loading the fine-tuned model for inference...")
qa_pipeline = pipeline("text-generation", model="./llama3-mcqa-lora", tokenizer=tokenizer)

# Example MCQA question
question = "What was the trend of the KOSPI on October 20, 2024?"
options = "(A) KOSPI rose (B) KOSPI fell (C) No change (D) KOSDAQ rose"

# Generate the answer
prompt = f"{question}\n{options}\nAnswer:"
result = qa_pipeline(prompt)

print("Generated Answer:", result[0]["generated_text"])
