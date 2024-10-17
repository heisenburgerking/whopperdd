from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 모델과 토크나이저 로드
model_name = "meta-llama/Llama-3.1-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

# 간단한 금융 관련 프롬프트 테스트
prompt = "What is the importance of diversification in investment?"

# 입력 인코딩
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

# 출력 생성
outputs = model.generate(**inputs, max_length=200, num_return_sequences=1)

# 출력 디코딩 및 출력
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Prompt: {prompt}\n")
print(f"Response: {response}")
