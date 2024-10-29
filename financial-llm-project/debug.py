from src.data_collection.krx_crawler import KRXCrawler
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

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())