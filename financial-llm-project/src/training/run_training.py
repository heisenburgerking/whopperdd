from trainer import FinancialDataTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        trainer = FinancialDataTrainer(
            model_name="heisenburgerking/llama3.1-8b",
            output_dir="models/financial-llm",
            batch_size=4,
            gradient_accumulation_steps=4,
            num_train_epochs=3,
            learning_rate=2e-5
        )
        
        trainer.train()
        
    except Exception as e:
        logger.error(f"Training failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 