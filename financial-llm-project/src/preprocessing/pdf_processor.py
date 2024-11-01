import PyPDF2
import pandas as pd
import re
from typing import List, Dict
from konlpy.tag import Kkma

class PDFProcessor:
    def __init__(self):
        self.raw_text = ""
        self.kkma = Kkma()
        
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
    
    def split_into_chunks(self, text: str, max_length: int = 2048) -> List[str]:
        """텍스트를 의미 단위로 분할하고 적절한 길이로 청크화합니다."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:  # 빈 문단 건너뛰기
                continue
                
            # 문단이 max_length를 초과하면 문장 단위로 분할
            if len(para) > max_length:
                sentences = self.kkma.sentences(para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                        
                    if len(current_chunk) + len(sent) <= max_length:
                        current_chunk += sent + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent + " "
            else:
                if len(current_chunk) + len(para) <= max_length:
                    current_chunk += para + " "
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = para + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return [chunk for chunk in chunks if len(chunk) >= 100]  # 너무 짧은 청크 제거
    
    def create_qa_pairs(self, chunks: List[str]) -> List[Dict]:
        """청크를 Q&A 형식으로 변환합니다."""
        qa_pairs = []
        
        for chunk in chunks:
            # 불필요한 섹션 제외
            if any(skip in chunk.lower() for skip in ['참고문헌', '목차', 'references', 'table of contents']):
                continue
                
            # 의미 있는 내용인지 확인
            if len(chunk.split()) < 20:  # 단어 수가 너무 적으면 제외
                continue
                
            qa_pair = {
                "instruction": "다음 경제 논문의 내용을 이해하고 관련 질문에 답변할 수 있도록 학습하세요.",
                "input": chunk,
                "output": "네, 이해했습니다. 해당 내용에 대해 질문해 주시면 답변하도록 하겠습니다."
            }
            qa_pairs.append(qa_pair)
            
        return qa_pairs
    
    def _generate_summary(self, text: str) -> str:
        """텍스트의 요약을 생성합니다."""
        # 여기에 요약 로직 구현 필요
        # 예: 핵심 문장 추출 또는 외부 요약 모델 사용
        # 임시로 첫 문장 반환
        first_sentence = self.kkma.sentences(text)[0]
        return first_sentence
    
    def save_to_jsonl(self, qa_pairs: List[Dict], output_path: str):
        """Q&A 쌍을 JSONL 형식으로 저장합니다."""
        df = pd.DataFrame(qa_pairs)
        df.to_json(output_path, orient='records', lines=True, force_ascii=False)