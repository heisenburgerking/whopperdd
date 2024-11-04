from openai import OpenAI
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time
import backoff

client = OpenAI(api_key='_QA')

@backoff.on_exception(backoff.expo, 
                     Exception,
                     max_tries=8)  # 최대 8번 재시도
def generate_mcqa(article):
    try:
        prompt = f"""
        Please generate Korean multiple-choice questions and respective answers based on the following news article.
        The question should be in Korean, relevant to the article's content, and include one correct answer and several incorrect options.
        And then, generate the correct answer in the format '### Answer: [Correct answer here]'.
        Use the format '### Question: [Your question here]' for the question. Use the format '### Answer: [Correct answer here]' for the correct answer.
        BEAR IN MIND THAT ALL TEXT YOU GENERATE AS QUESTION AND ANSWER SHOULD BE IN KOREAN.

        News Article: {article}
        ### Question:
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Korean multiple-choice questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        # 응답을 파싱하여 구조화
        question_part = raw_response.split('### Answer:')[0].replace('### Question:', '').strip()
        answer_part = raw_response.split('### Answer:')[1].strip()
        
        return {
            "question": question_part,
            "answer": answer_part
        }
        
    except Exception as e:
        if "up_X3" in str(e):
            print(f"\n레이트 리밋 발생. 잠시 대기 후 재시도합니다...")
            time.sleep(3)  # 20초 대기
            raise  # backoff가 재시도하도록 예외를 다시 발생
        raise  # 다른 예외는 그대로 전파

def process_article(row):
    try:
        article = row['content']
        mcqa_result = generate_mcqa(article)
        return {
            'article': article,
            'question': mcqa_result['question'],
            'answer': mcqa_result['answer'],
            'status': 'success'
        }
    except Exception as e:
        print(f"\n에러 발생: {str(e)}")
        return {
            'article': article,
            'question': None,
            'answer': None,
            'status': f'error: {str(e)}'
        }

# Path configurations
input_file_path = 'C:\\\cleaned_data_b2.csv'
output_folder_path = 'C:X\\results\\'

# Batch size configuration
batch_size = 300

# CSV 파일 읽기
try:
    with open(input_file_path, 'r', encoding='cp949') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
except UnicodeDecodeError:
    # cp949로 읽기 실패시 euc-kr 시도
    with open(input_file_path, 'r', encoding='euc-kr') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

# 전체 진행 상황을 보여주는 프로그레스 바와 함께 배치 처리
total_batches = (len(rows) + batch_size - 1) // batch_size
with tqdm(total=len(rows), desc="전체 진행률") as pbar:
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        batch_number = i // batch_size + 1
        
        print(f"\n배치 {batch_number}/{total_batches} 처리 중...")
        
        # 각 배치의 진행 상황을 보여주는 프로그레스 바
        batch_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = list(executor.map(process_article, batch))
            for result in futures:
                batch_results.append(result)
                pbar.update(1)
        
        output_file_path = f"{output_folder_path}mcqa_results_batch_{batch_number}.json"
        with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(batch_results, jsonfile, ensure_ascii=False, indent=4)
        
        print(f"배치 {batch_number} 저장 완료: {output_file_path}")

print("\n모든 처리가 완료되었습니다!")