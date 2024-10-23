from transformers import Trainer, TrainingArguments
from src.model.llama_loader import load_llama_model
from src.data_processing.data_cleaner import create_dataset
import pandas as pd

def fine_tune_model(model_name, dataset, output_dir):
    tokenizer, model = load_llama_model(model_name)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    trainer.train()
    trainer.save_model()

if __name__ == "__main__":
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    dataset = create_dataset(pd.read_csv("data/processed/cleaned_financial_news.csv"))
    output_dir = "models/fine_tuned"
    
    fine_tune_model(model_name, dataset, output_dir)
