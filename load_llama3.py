from transformers import AutoTokenizer, AutoModelForCausalLM
import os

# Use your valid Hugging Face token
os.environ['HUGGINGFACE_HUB_TOKEN'] = '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'
os.environ["HUGGINGFACE_TOKEN"] = "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"


model_name = "meta-llama/Llama-3.1-8B-Instruct"


### 
import logging
from transformers import logging as hf_logging

# Enable logging
hf_logging.set_verbosity_info()

# Load tokenizer and model
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("Tokenizer loaded.")

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(model_name)
print("Model loaded.")

input_text = "What is the capital of France?"
inputs = tokenizer(input_text, return_tensors="pt")

print("Generating output...")
outputs = model.generate(**inputs)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("Response:", response)

