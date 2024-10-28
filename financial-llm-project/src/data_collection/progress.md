# 데이터 수집 진행 상황

## 1. KRX 데이터 수집 [`krx_crawler.py`] ✅
- **구현 완료**:
  - 주식 기본 정보 수집 (`get_stock_fundamental`)
  - 재무제표 데이터 수집 (`get_financial_statements`)
  - 주가 히스토리 데이터 수집 (`get_stock_price_history`)
  - 데이터 저장 기능 (`save_to_file`)

- **사용 방법**:
``` python
from krx_crawler import KRXCrawler
async def main():
crawler = KRXCrawler()
# 삼성전자(005930) 데이터 수집 예시
stock_code = "005930"
# 기본 정보 수집
fundamental_data = await crawler.get_stock_fundamental(stock_code)
crawler.save_to_file(fundamental_data, f"{stock_code}fundamental")
# 재무제표 수집
financial_data = await crawler.get_financial_statements(stock_code)
crawler.save_to_file(financial_data, f"{stock_code}financial")
# 주가 히스토리 수집
price_history = await crawler.get_stock_price_history(
stock_code,
start_date="20230101",
end_date="20231231"
)
crawler.save_to_file(price_history, f"{stock_code}price_history")
```

## 2. 뉴스 데이터 수집 [`news_crawler.py`] 🚧
- **구현 완료**:
  - 네이버 금융 뉴스 기사 수집 (`get_naver_finance_news`)
  - 뉴스 본문 수집 (`_get_article_content`)
  - 텍스트 정제 (`_clean_text`)
  - 데이터 저장 기능 (`save_to_file`)

- **사용 방법**:
``` python
from news_crawler import NewsCrawler
async def main():
crawler = NewsCrawler()
# 네이버 금융 뉴스 수집 예시
keywords = ["삼성전자", "네이버"]
news_list = await crawler.get_naver_finance_news(keywords)
crawler.save_to_file(news_list, "naver_finance_news")
```

## 3. 금융 교육 자료 수집 [`education_crawler.py`] 📝
- **구현 예정**:
  - 경제학 교과서 및 전문 서적 내용 수집
  - 금융 용어 사전 및 개념 설명 수집
  - 재무회계 원칙 및 이론 자료 수집
  - 투자 이론 및 전략 자료 수집

## 4. 문제-답변 데이터 수집 [`qa_crawler.py`] 📝
- **구현 예정**:
  - CFA, 증권분석사 등 금융 자격증 기출문제 수집
  - 경제/금융 관련 퀴즈 및 연습문제 수집
  - 실제 투자 사례 연구 자료 수집

## 진행 상태 표시
- ✅ 완료
- 🚧 진행 중
- 📝 예정
- ❌ 보류/중단

## 우선순위
1. `news_crawler.py` 구현
   - 네이버 금융, 한국경제, 매일경제 등 주요 경제 뉴스 사이트 크롤링
   - 텍스트 데이터 정제 및 저장

2. `education_crawler.py` 구현
   - 공개된 금융 교육 자료 수집
   - PDF, 웹 문서 등 다양한 형식의 데이터 처리

3. `qa_crawler.py` 구현
   - 기출문제 및 예제 문제 수집
   - Q&A 형식으로 데이터 구조화

## 다음 작업
- [x] `news_crawler.py` 기본 구조 설계
- [x] 네이버 뉴스 크롤링 규칙 정의
- [ ] 다른 뉴스 사이트 크롤링 규칙 정의
- [ ] 한국경제, 매일경제 크롤러 추가
- [ ] 애널리스트 리포트 수집 기능 추가