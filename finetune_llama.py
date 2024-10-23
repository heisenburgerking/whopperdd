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
import sys
import os

# wandb 비활성화
os.environ["WANDB_DISABLED"] = "true"

# Step 1: Load the Tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", use_fast=True)

# Ensure the tokenizer has a pad token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Step 2: Load the Training Data
print("Loading training data...")
try:
    with open("training_data.json", "r") as f:
        training_data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON format in training_data.json: {e}")
    print("Please ensure the file contains valid JSON data and not Git LFS pointers")
    sys.exit(1)
except FileNotFoundError:
    print("Error: training_data.json file not found")
    sys.exit(1)

# Step 3: Tokenize the Data
def tokenize_data(data):
    tokenized_data = []
    for entry in data:
        # 입력 텍스트 토크나이징
        inputs = tokenizer(
            entry["input"],
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt"
        )
        
        # 타겟 텍스트 토크나이징
        labels = tokenizer(
            entry["target"],
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt"
        )

        # -100으로 패딩 토큰 마스킹 (손실 계산에서 제외)
        label_ids = labels["input_ids"].clone()
        label_ids[label_ids == tokenizer.pad_token_id] = -100

        tokenized_data.append({
            "input_ids": inputs["input_ids"].squeeze(0),
            "attention_mask": inputs["attention_mask"].squeeze(0),
            "labels": label_ids.squeeze(0)
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
        item = {
            "input_ids": self.data[idx]["input_ids"].clone().detach(),
            "attention_mask": self.data[idx]["attention_mask"].clone().detach(),
            "labels": self.data[idx]["labels"].clone().detach()
        }
        # 모든 텐서를 float16으로 변환
        for k, v in item.items():
            if isinstance(v, torch.Tensor):
                item[k] = v.to(dtype=torch.long)  # 정수 텐서로 변환
        return item

print("Creating DataLoader...")
dataset = FinancialDataset(tokenized_data)
dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

# GPU 메모리 설정 추가
torch.cuda.empty_cache()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Step 5: Load the LLaMA Model (CPU-Compatible)
print("Loading LLaMA model...")
model = LlamaForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    use_cache=False  # 그래디언트 체크포인팅과 호환되도록
)

# 모델을 학습 모드로 설정
model.train()
model.gradient_checkpointing_enable()  # 그래디언트 체크포인팅 활성화

# 모델 파라미터 학습 가능하도록 설정
for param in model.parameters():
    param.requires_grad = True

# Step 6: Apply LoRA for Parameter-Efficient Fine-Tuning
lora_config = LoraConfig(
    r=4,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",  # 태스크 타입 명시
    inference_mode=False  # 학습 모드 활성화
)
model = get_peft_model(model, lora_config)

# Step 7: Define Training Arguments
print("Setting up training arguments...")
training_args = TrainingArguments(
    output_dir="./llama3-mcqa-lora",
    evaluation_strategy="epoch",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    num_train_epochs=3,
    learning_rate=2e-5,
    logging_dir="./logs",
    save_steps=500,
    save_total_limit=2,
    fp16=True,
    gradient_checkpointing=True,
    report_to=[],
    remove_unused_columns=False,  # 추가
    label_names=["labels"]  # 추가
)

# Step 8: Initialize the Trainer and Train the Model
print("Initializing Trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=lambda data: {
        'input_ids': torch.stack([f['input_ids'] for f in data]),
        'attention_mask': torch.stack([f['attention_mask'] for f in data]),
        'labels': torch.stack([f['labels'] for f in data])
    }
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
