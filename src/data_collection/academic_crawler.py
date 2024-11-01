from scholarly import scholarly
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import logging
from typing import Dict, List, Optional
import time
from random import uniform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AcademicPaperCrawler:
    def __init__(self):
        self.setup_scholarly()
        
    def setup_scholarly(self):
        """Scholarly 설정을 초기화합니다."""
        try:
            # Chrome 옵션 설정
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')  # 헤드리스 모드
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Chrome 드라이버 설정
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # scholarly에 selenium 드라이버 설정
            scholarly.use_selenium(driver)
            
            # 기본 설정
            scholarly.set_timeout(30)
            scholarly.set_retries(5)
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Scholarly 설정 중 오류 발생: {str(e)}")

    def get_paper_details(self, pub) -> Optional[Dict]:
        """논문의 상세 정보를 수집합니다."""
        try:
            filled_pub = scholarly.fill(pub)
            time.sleep(uniform(2, 4))
            
            paper_info = {
                'title': filled_pub.bib.get('title', ''),
                'abstract': filled_pub.bib.get('abstract', ''),
                'year': filled_pub.bib.get('year', ''),
                'url': filled_pub.bib.get('url', '') or filled_pub.bib.get('eprint', ''),
                'authors': filled_pub.bib.get('author', ''),
                'journal': filled_pub.bib.get('journal', ''),
                'citations': getattr(filled_pub, 'citedby', 0)
            }
            
            logger.info(f"논문 수집: {paper_info['title']}")
            return paper_info
            
        except Exception as e:
            logger.error(f"논문 정보 수집 중 오류 발생: {str(e)}")
            return None

    def search_papers(self, keyword: str, limit: int = 50) -> List[Dict]:
        """키워드로 논문을 검색합니다."""
        papers = []
        try:
            search_query = scholarly.search_pubs(keyword)
            for _ in range(limit):
                try:
                    pub = next(search_query)
                    paper_info = self.get_paper_details(pub)
                    if paper_info:
                        papers.append(paper_info)
                    time.sleep(uniform(3, 5))
                except StopIteration:
                    break
                except Exception as e:
                    logger.error(f"개별 논문 처리 중 오류: {str(e)}")
                    time.sleep(uniform(5, 8))
                    continue
                    
        except Exception as e:
            logger.error(f"논문 검색 중 오류 발생: {str(e)}")
            
        return papers

    def get_korean_keywords(self) -> List[str]:
        """검색할 한국어 키워드 목록을 반환합니다."""
        return [
            "한국 금융시장", "기업재무 한국", "주식시장 분석",
            "재무회계", "투자론", "기업가치평가",
            "금융공학", "파생상품", "위험관리",
            "포트폴리오 관리", "자산가격결정", "시장효율성"
        ]

    def crawl_academic_papers(self, papers_per_keyword: int = 50) -> pd.DataFrame:
        """모든 키워드에 대해 논문을 수집합니다."""
        all_papers = []
        keywords = self.get_korean_keywords()

        for keyword in keywords:
            logger.info(f"키워드 '{keyword}' 관련 논문 수집 중...")
            try:
                papers = self.search_papers(keyword, papers_per_keyword)
                all_papers.extend(papers)
                time.sleep(uniform(5, 8))  # 키워드 간 딜레이 증가
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 처리 중 오류 발생: {str(e)}")
                time.sleep(uniform(10, 15))  # 오류 발생 시 더 긴 딜레이
                continue

        # DataFrame 생성 및 전처리
        df = pd.DataFrame(all_papers)
        if not df.empty:
            df = df.drop_duplicates(subset=['title', 'year'])
            df = df.sort_values('year', ascending=False)
            
        return df

def save_papers_data(df: pd.DataFrame, output_path: str):
    """수집된 논문 데이터를 CSV 파일로 저장합니다."""
    try:
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"데이터가 성공적으로 저장됨: {output_path}")
    except Exception as e:
        logger.error(f"데이터 저장 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import os
    
    try:
        crawler = AcademicPaperCrawler()
        papers_data = crawler.crawl_academic_papers()
        
        if not papers_data.empty:
            output_path = os.path.join(os.path.dirname(__file__), '..', '..', 
                                     'data', 'raw', 'academic_papers.csv')
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            save_papers_data(papers_data, output_path)
            logger.info(f"총 {len(papers_data)} 개의 논문 데이터 수집 완료")
        else:
            logger.error("수집된 데이터가 없습니다.")
            
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
