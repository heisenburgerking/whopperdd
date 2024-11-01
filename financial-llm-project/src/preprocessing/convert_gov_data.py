import json
import os
import logging
from typing import List, Dict
import pandas as pd

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovDataProcessor:
    def __init__(self):
        self.raw_data = []
        
    def load_data(self, input_path: str):
        """정부 데이터를 로드합니다."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            logger.info(f"Loaded {len(self.raw_data)} records from {input_path}")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
            
    def process_bok_data(self, data: Dict) -> List[Dict]:
        """한국은행 통계 데이터를 Q&A 형식으로 변환합니다."""
        qa_pairs = []
        
        try:
            title = data['title']
            content = data['content']
            date = data['date']
            raw_data = data['raw_data']
            
            # 통계 항목의 기본 이름 (날짜 제외)
            base_title = title.split(' - ')[0]
            item_name = title.split(' - ')[1] if ' - ' in title else title
            
            # 이미 처리된 통계 항목인지 확인하기 위한 키 생성
            stat_key = f"{base_title}_{item_name}"
            
            # 해당 통계를 처음 처리하는 경우에만 일반적인 질문 추가
            if not hasattr(self, 'processed_stats'):
                self.processed_stats = set()
                
            if stat_key not in self.processed_stats:
                self.processed_stats.add(stat_key)
                
                # 통계 해석 질문 (한 번만 생성)
                qa_pairs.append({
                    "instruction": f"{base_title}의 {item_name}이란 무엇입니까?",
                    "input": "",
                    "output": f"이는 한국은행에서 발표하는 공식 통계로, {content}"
                })
                
                # 단위 관련 질문 (한 번만 생성)
                qa_pairs.append({
                    "instruction": f"{base_title}의 {item_name}은 어떤 단위로 측정됩니까?",
                    "input": "",
                    "output": f"측정 단위는 {raw_data['unit']}입니다."
                })
            
            # 수치 관련 질문 (날짜별로 생성)
            qa_pairs.append({
                "instruction": f"{base_title}의 {item_name}은 {date} 기준으로 얼마입니까?",
                "input": "",
                "output": f"{content}"
            })
                
        except Exception as e:
            logger.error(f"Error processing BOK data: {str(e)}")
            
        return qa_pairs
    
    def process_dart_data(self, data: Dict) -> List[Dict]:
        """DART 공시 데이터를 Q&A 형식으로 변환합니다."""
        qa_pairs = []
        
        try:
            corp_name = data['corp_name']
            title = data['title']
            date = data['date']
            content = data['content']
            disclosure_type = data['raw_data']['disclosure_type']
            
            # 내용이 있는 경우에만 처리
            if content.strip():
                # 1. 공시 내용 관련 질문
                qa_pairs.append({
                    "instruction": f"{corp_name}의 {title}에 대해 설명해주세요.",
                    "input": "",
                    "output": f"{date}에 공시된 내용입니다:\n{content}"
                })
                
                # 2. 기업 관련 질문
                qa_pairs.append({
                    "instruction": f"{corp_name}의 {disclosure_type}은 어떤 내용을 담고 있나요?",
                    "input": "",
                    "output": f"{content}\n\n이는 {date}에 공시된 내용입니다."
                })
                
                # 3. 재무정보가 있는 경우
                if data['raw_data'].get('financial_data') and data['raw_data']['financial_data'].get('list'):
                    financial_data = data['raw_data']['financial_data']['list']
                    qa_pairs.append({
                        "instruction": f"{corp_name}의 주요 재무정보를 알려주세요.",
                        "input": "",
                        "output": f"공시된 재무정보는 다음과 같습니다:\n{str(financial_data)}"
                    })
                    
        except Exception as e:
            logger.error(f"Error processing DART data: {str(e)}")
            
        return qa_pairs
    
    def convert_to_qa_pairs(self) -> List[Dict]:
        """전체 데이터를 Q&A 형식으로 변환합니다."""
        all_qa_pairs = []
        
        for data in self.raw_data:
            try:
                if data['source'] == 'BOK':
                    qa_pairs = self.process_bok_data(data)
                elif data['source'] == 'DART':
                    qa_pairs = self.process_dart_data(data)
                else:
                    logger.warning(f"Unknown data source: {data['source']}")
                    continue
                    
                all_qa_pairs.extend(qa_pairs)
                
            except Exception as e:
                logger.error(f"Error converting data to QA pairs: {str(e)}")
                continue
                
        return all_qa_pairs
    
    def save_qa_pairs(self, qa_pairs: List[Dict], output_path: str):
        """Q&A 쌍을 JSONL 형식으로 저장합니다."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df = pd.DataFrame(qa_pairs)
            df.to_json(output_path, orient='records', lines=True, force_ascii=False)
            logger.info(f"Saved {len(qa_pairs)} QA pairs to {output_path}")
        except Exception as e:
            logger.error(f"Error saving QA pairs: {str(e)}")
            raise

def main():
    input_path = "../../data/raw/gov_data.json"
    output_path = "../../data/processed/gov_qa_pairs.jsonl"
    
    processor = GovDataProcessor()
    processor.load_data(input_path)
    qa_pairs = processor.convert_to_qa_pairs()
    processor.save_qa_pairs(qa_pairs, output_path)

if __name__ == "__main__":
    main() 