import requests
from bs4 import BeautifulSoup

def crawl_government_data():
    sources = {
        'BOK': 'https://www.bok.or.kr/portal/bbs/B0000005/list.do',  # 한국은행
        'FSS': 'http://www.fss.or.kr/fss/bbs/B0000188/list.do',     # 금융감독원
        'KRX': 'http://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd'  # 한국거래소
    }
    
    data = []
    for source, url in sources.items():
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # 각 사이트별 크롤링 로직 구현
        # ...
    
    return data 