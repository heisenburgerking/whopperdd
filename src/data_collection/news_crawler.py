import requests
from bs4 import BeautifulSoup
import pandas as pd

def crawl_financial_news():
    news_sources = {
        'fn_guide': 'http://www.fnguide.com/wp/',
        'investing': 'https://kr.investing.com/',
        'hankyung': 'https://www.hankyung.com/economy'
    }
    
    news_data = []
    for source, url in news_sources.items():
        # 각 뉴스 사이트별 크롤링 로직 구현
        # ...
    
    return pd.DataFrame(news_data) 