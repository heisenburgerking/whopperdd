import PyPDF2
import pandas as pd
import re
from typing import List, Dict
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')

class PDFProcessor:
    def __init__(self):
        self.raw_text = ""
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF 파일에서 텍스트를 추출합니다."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        self.raw_text = text
        return text
    
    def clean_text(self, text: str) -> str:
        """추출된 텍스트를 정제합니다."""
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        # 특수문자 제거 (단, 한글, 영문, 숫자, 기본 문장부호는 유지)
        text = re.sub(r'[^\w\s\.,!?;:\'\"가-힣]', '', text)
        return text.strip()
    
    def split_into_chunks(self, text: str, max_length: int = 512) -> List[str]:
        """텍스트를 문장 단위로 분할하고 적절한 길이로 청크화합니다."""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def create_qa_pairs(self, chunks: List[str]) -> List[Dict]:
        """청크를 Q&A 형식으로 변환합니다."""
        qa_pairs = []
        
        for chunk in chunks:
            # 청크의 주요 내용을 기반으로 질문-답변 쌍 생성
            qa_pair = {
                "instruction": f"다음 경제 논문의 내용을 요약해주세요:\n\n{chunk}",
                "input": "",
                "output": chunk
            }
            qa_pairs.append(qa_pair)
            
        return qa_pairs
    
    def save_to_jsonl(self, qa_pairs: List[Dict], output_path: str):
        """Q&A 쌍을 JSONL 형식으로 저장합니다."""
        df = pd.DataFrame(qa_pairs)
        df.to_json(output_path, orient='records', lines=True, force_ascii=False) 