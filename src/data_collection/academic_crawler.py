import logging
from scholarly import scholarly, ProxyGenerator
import pandas as pd
from typing import List, Dict
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import random

class AcademicCrawler:
    def __init__(self):
        self.logger = self._setup_logger()
        self._setup_scholarly()
        self._ensure_data_directory()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _setup_scholarly(self):
        try:
            # scholarly 기본 설정
            scholarly.set_timeout(10)
            scholarly.set_retries(5)
            
            # Chrome 설정
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # ProxyGenerator 설정
            pg = ProxyGenerator()
            success = pg.FreeProxies()  # 무료 프록시 사용
            
            if success:
                scholarly.use_proxy(pg)
                self.logger.info("Scholarly 프록시 설정 완료")
            else:
                self.logger.warning("프록시 설정 실패, 프록시 없이 진행합니다")
                
        except Exception as e:
            self.logger.error(f"Scholarly 설정 중 오류 발생: {str(e)}")

    def _ensure_data_directory(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
        os.makedirs(data_dir, exist_ok=True)

    def get_paper_details(self, pub) -> Dict:
        try:
            # 논문의 전체 정보를 가져옴
            filled_pub = scholarly.fill(pub)
            
            # 논문 기본 정보 추출
            paper_info = {
                'title': filled_pub['bib'].get('title', ''),
                'authors': filled_pub['bib'].get('author', []),
                'year': filled_pub['bib'].get('year', ''),
                'abstract': filled_pub['bib'].get('abstract', ''),
                'venue': filled_pub['bib'].get('venue', ''),
                'citations': filled_pub.get('num_citations', 0),
                'url': filled_pub['bib'].get('url', '')
            }
            return paper_info
            
        except Exception as e:
            self.logger.error(f"논문 정보 수집 중 오류 발생: {str(e)}")
            return {}

    def search_papers(self, keyword: str, limit: int = 10) -> List[Dict]:
        papers = []
        try:
            search_query = scholarly.search_pubs(keyword)
            for i, pub in enumerate(search_query):
                if i >= limit:
                    break
                    
                try:
                    # 각 논문 수집 시도마다 딜레이 추가
                    time.sleep(random.uniform(2, 5))  # 2-5초 랜덤 딜레이
                    
                    paper_info = self.get_paper_details(pub)
                    if paper_info:
                        papers.append(paper_info)
                        self.logger.info(f"논문 정보 수집 완료: {paper_info['title']}")
                        
                    # 5개의 논문마다 긴 딜레이 추가
                    if (i + 1) % 5 == 0:
                        time.sleep(random.uniform(10, 15))  # 10-15초 랜덤 딜레이
                        
                except Exception as e:
                    self.logger.error(f"개별 논문 정보 수집 중 오류 발생: {str(e)}")
                    # 오류 발생 시 더 긴 딜레이 추가
                    time.sleep(random.uniform(20, 30))
                    continue
                
        except Exception as e:
            self.logger.error(f"논문 검색 중 오류 발생: {str(e)}")
                
            return papers

    def save_to_file(self, data: List[Dict], filename: str):
        try:
            df = pd.DataFrame(data)
            save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'data', 'raw', f"{filename}.csv")
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"데이터를 {filename}.csv에 저장했습니다.")
        except Exception as e:
            self.logger.error(f"파일 저장 중 오류 발생: {str(e)}")

    def crawl_academic_papers(self, keywords: List[str] = None, papers_per_keyword: int = 10) -> List[Dict]:
        if keywords is None:
            keywords = ['한국 금융시장', '주식시장 분석', '금융 정책']
            
        all_papers = []
        
        for i, keyword in enumerate(keywords):
            self.logger.info(f"키워드 '{keyword}' 관련 논문 수집 중... ({i+1}/{len(keywords)})")
            
            # 키워드마다 다른 프록시 사용 시도
            if i > 0:  # 첫 번째 키워드 이후
                try:
                    pg = ProxyGenerator()
                    success = pg.FreeProxies()
                    if success:
                        scholarly.use_proxy(pg)
                        self.logger.info("새로운 프록시로 전환")
                    time.sleep(random.uniform(15, 20))  # 프록시 전환 후 딜레이
                except Exception as e:
                    self.logger.error(f"프록시 전환 중 오류: {str(e)}")
            
            papers = self.search_papers(keyword, papers_per_keyword)
            all_papers.extend(papers)
            
            # 키워드 사이에 긴 딜레이
            if i < len(keywords) - 1:  # 마지막 키워드가 아닌 경우
                time.sleep(random.uniform(30, 45))
                
        self.save_to_file(all_papers, 'academic_papers')
        return all_papers

if __name__ == "__main__":
    crawler = AcademicCrawler()
    papers_data = crawler.crawl_academic_papers() 