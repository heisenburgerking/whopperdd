from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
import torch
import json
import jsonlines
from datasets import Dataset
import logging
import os
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialDataTrainer:
    def __init__(
        self,
        model_name: str = "heisenburgerking/llama3.1-8b",
        output_dir: str = "models/financial-llm",
        batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        num_train_epochs: int = 3,
        learning_rate: float = 2e-5,
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.num_train_epochs = num_train_epochs
        self.learning_rate = learning_rate
        
        # GPU 사용 가능 여부 확인
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        self._setup_model_and_tokenizer()
        
    def _setup_model_and_tokenizer(self):
        """모델과 토크나이저 설정"""
        logger.info("Loading tokenizer and model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Special tokens 설정
        special_tokens = {"pad_token": "[PAD]"}
        self.tokenizer.add_special_tokens(special_tokens)
        self.model.resize_token_embeddings(len(self.tokenizer))

    def _load_and_preprocess_data(self) -> Dataset:
        """데이터 로드 및 전처리"""
        logger.info("Loading and preprocessing data...")
        
        # 데이터 로드
        train_data = []
        
        # 논문 데이터 로드
        with jsonlines.open("data/processed/paper_qa_pairs.jsonl") as reader:
            for item in reader:
                train_data.append({
                    "instruction": item["instruction"],
                    "input": item["input"],
                    "output": item["output"]
                })
        
        # 정부/국가 데이터 로드
        with jsonlines.open("data/processed/gov_qa_pairs.jsonl") as reader:
            for item in reader:
                train_data.append({
                    "instruction": item["instruction"],
                    "input": item["input"],
                    "output": item["output"]
                })
        
        # 기사 데이터 로드
        with open("data/processed/nfcr_data.json", "r", encoding="utf-8") as f:
            nfcr_data = json.load(f)
            train_data.extend(nfcr_data)
        
        # 데이터셋 포맷팅
        formatted_data = []
        for item in train_data:
            prompt = f"{item['instruction']}\n\n{item['input']}\n### 정답:"
            response = f"{item['output']}\n"
            formatted_data.append({
                "text": f"{prompt}{response}"
            })
        
        return Dataset.from_list(formatted_data)

    def train(self):
        """모델 학습 실행"""
        logger.info("Starting training process...")
        
        # 데이터 로드
        train_dataset = self._load_and_preprocess_data()
        
        # 학습 인자 설정
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            per_device_train_batch_size=self.batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            num_train_epochs=self.num_train_epochs,
            learning_rate=self.learning_rate,
            fp16=True,
            logging_steps=100,
            save_strategy="epoch",
            save_total_limit=2,
            remove_unused_columns=False,
            push_to_hub=True,
            hub_model_id="financial-llm"
        )
        
        # Data collator 설정
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Trainer 초기화 및 학습
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        logger.info("Training started...")
        trainer.train()
        
        # 모델 저장
        logger.info("Saving model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        logger.info("Training completed successfully!")
