from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_llama_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
    return tokenizer, model

def generate_response(tokenizer, model, prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_length=200, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    tokenizer, model = load_llama_model(model_name)
    
    prompt = "What is the importance of diversification in investment?"
    response = generate_response(tokenizer, model, prompt)
    print(f"Prompt: {prompt}\n")
    print(f"Response: {response}")
