import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import re
from typing import List, Dict, Optional

class NewsCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('NewsCrawler')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def get_naver_finance_news(
        self,
        keywords: List[str],
        days: int = 7,
        max_pages: int = 10
    ) -> List[Dict]:
        """네이버 금융 뉴스 수집"""
        news_list = []
        
        for keyword in keywords:
            self.logger.info(f"Collecting news for keyword: {keyword}")
            
            for page in range(1, max_pages + 1):
                url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sort=1&ds={days}&start={page}"
                
                try:
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    news_items = soup.select("div.news_wrap.api_ani_send")
                    
                    if not news_items:
                        break
                        
                    for item in news_items:
                        try:
                            title = item.select_one("a.news_tit").text
                            link = item.select_one("a.news_tit")["href"]
                            source = item.select_one("a.info.press").text
                            date_text = item.select_one("span.info").text
                            
                            # 본문 내용 수집
                            article_content = await self._get_article_content(link)
                            
                            news_list.append({
                                "keyword": keyword,
                                "title": title,
                                "content": article_content,
                                "source": source,
                                "date": date_text,
                                "url": link
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Error parsing news item: {str(e)}")
                            continue
                            
                    time.sleep(1)  # 크롤링 간격 조절
                    
                except Exception as e:
                    self.logger.error(f"Error fetching page {page} for {keyword}: {str(e)}")
                    continue
                    
        return news_list

    async def _get_article_content(self, url: str) -> str:
        """뉴스 기사 본문 수집"""
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 네이버 뉴스인 경우
            if "news.naver.com" in url:
                content = soup.select_one("#dic_area")
                if content:
                    return self._clean_text(content.text)
            
            # 다른 언론사 사이트인 경우
            content = soup.find(['article', 'div'], class_=re.compile('article|content|body'))
            if content:
                return self._clean_text(content.text)
                
            return ""
            
        except Exception as e:
            self.logger.error(f"Error fetching article content: {str(e)}")
            return ""

    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        text = re.sub(r'\s+', ' ', text)  # 연속된 공백 제거
        text = re.sub(r'[\n\t\r]', ' ', text)  # 개행문자 제거
        return text.strip()

    def save_to_file(self, data: List[Dict], filename: str) -> None:
        """수집된 뉴스 데이터를 파일로 저장"""
        try:
            df = pd.DataFrame(data)
            df.to_csv(f"data/raw/{filename}.csv", index=False, encoding='utf-8-sig')
            self.logger.info(f"Successfully saved {len(data)} news articles to {filename}.csv")
        except Exception as e:
            self.logger.error(f"Error saving data to file {filename}: {str(e)}")

