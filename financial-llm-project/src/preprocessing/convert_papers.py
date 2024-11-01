from pdf_processor import PDFProcessor
import os
import json
from typing import List, Dict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_qa_pair(qa_pair: Dict) -> bool:
    """QA 쌍의 유효성을 검사합니다."""
    if not all(key in qa_pair for key in ['instruction', 'input', 'output']):
        return False
    if not qa_pair['input'] or len(qa_pair['input']) < 100:
        return False
    return True

def process_papers(input_dir: str, output_path: str):
    processor = PDFProcessor()
    all_qa_pairs = []
    processed_files = 0
    failed_files = 0
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # PDF 파일들을 처리
        for filename in os.listdir(input_dir):
            if not filename.endswith('.pdf'):
                continue
                
            pdf_path = os.path.join(input_dir, filename)
            logger.info(f"Processing {filename}...")
            
            try:
                # PDF에서 텍스트 추출
                text = processor.extract_text_from_pdf(pdf_path)
                if not text.strip():
                    logger.warning(f"No text extracted from {filename}")
                    failed_files += 1
                    continue
                
                # 텍스트 정제
                cleaned_text = processor.clean_text(text)
                
                # 청크로 분할
                chunks = processor.split_into_chunks(cleaned_text)
                logger.info(f"Created {len(chunks)} chunks from {filename}")
                
                # Q&A 쌍 생성
                qa_pairs = processor.create_qa_pairs(chunks)
                
                # QA 쌍 검증
                valid_qa_pairs = [qa for qa in qa_pairs if validate_qa_pair(qa)]
                all_qa_pairs.extend(valid_qa_pairs)
                
                processed_files += 1
                logger.info(f"Successfully processed {filename}: {len(valid_qa_pairs)} valid QA pairs")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                failed_files += 1
                continue
    
        # 결과 저장
        if all_qa_pairs:
            processor.save_to_jsonl(all_qa_pairs, output_path)
            logger.info(f"처리 완료!")
            logger.info(f"총 처리된 파일: {processed_files}")
            logger.info(f"실패한 파일: {failed_files}")
            logger.info(f"생성된 QA 쌍: {len(all_qa_pairs)}개")
        else:
            logger.error("No valid QA pairs generated!")
            
    except Exception as e:
        logger.error(f"Critical error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    input_dir = "./../../data/raw/papers"
    output_path = "./../../data/processed/paper_qa_pairs.jsonl"
    process_papers(input_dir, output_path)