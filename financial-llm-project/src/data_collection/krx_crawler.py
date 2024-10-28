import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

class KRXCrawler:
    def __init__(self):
        self.base_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('KRXCrawler')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def get_stock_fundamental(self, code: str) -> Dict:
        """주식 기본 정보 수집"""
        try:
            params = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
                "stockCode": code,
            }
            response = requests.get(self.base_url, params=params, headers=self.headers)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {code}: {str(e)}")
            return {}

    async def get_financial_statements(self, code: str) -> Dict:
        """재무제표 데이터 수집"""
        try:
            params = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT03901",
                "stockCode": code,
            }
            response = requests.get(self.base_url, params=params, headers=self.headers)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching financial statements for {code}: {str(e)}")
            return {}

    async def get_stock_price_history(
        self, 
        code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """주가 히스토리 데이터 수집"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        try:
            params = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT01701",
                "stockCode": code,
                "startDate": start_date,
                "endDate": end_date
            }
            response = requests.get(self.base_url, params=params, headers=self.headers)
            data = response.json()
            return pd.DataFrame(data.get('output', []))
        except Exception as e:
            self.logger.error(f"Error fetching price history for {code}: {str(e)}")
            return pd.DataFrame()

    def save_to_file(self, data: Dict, filename: str) -> None:
        """수집된 데이터를 파일로 저장"""
        try:
            if isinstance(data, pd.DataFrame):
                data.to_csv(f"data/raw/{filename}.csv", index=False, encoding='utf-8-sig')
            else:
                pd.DataFrame(data).to_csv(f"data/raw/{filename}.csv", index=False, encoding='utf-8-sig')
            self.logger.info(f"Successfully saved data to {filename}.csv")
        except Exception as e:
            self.logger.error(f"Error saving data to file {filename}: {str(e)}")

