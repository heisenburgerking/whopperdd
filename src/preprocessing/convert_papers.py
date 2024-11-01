from pdf_processor import PDFProcessor
import os

def process_papers(input_dir: str, output_path: str):
    processor = PDFProcessor()
    all_qa_pairs = []
    
    # PDF 파일들을 처리
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")
            
            # PDF에서 텍스트 추출
            text = processor.extract_text_from_pdf(pdf_path)
            
            # 텍스트 정제
            cleaned_text = processor.clean_text(text)
            
            # 청크로 분할
            chunks = processor.split_into_chunks(cleaned_text)
            
            # Q&A 쌍 생성
            qa_pairs = processor.create_qa_pairs(chunks)
            all_qa_pairs.extend(qa_pairs)
    
    # 결과 저장
    processor.save_to_jsonl(all_qa_pairs, output_path)
    print(f"처리 완료! {len(all_qa_pairs)}개의 Q&A 쌍이 생성되었습니다.")

if __name__ == "__main__":
    input_dir = "data/raw/papers"
    output_path = "data/processed/paper_qa_pairs.jsonl"
    process_papers(input_dir, output_path) 