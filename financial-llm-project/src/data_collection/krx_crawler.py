import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import os
import json

class KRXCrawler:
    def __init__(self):
        self.base_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.logger = self._setup_logger()
        self._ensure_data_directory()  # 생성자에 추가
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('KRXCrawler')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _ensure_data_directory(self):
        """데이터 저장 디렉토리 생성"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
        os.makedirs(data_dir, exist_ok=True)

    async def get_stock_fundamental(self, code: str) -> Dict:
        """주식 기본 정보 수집"""
        try:
            params = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
                "stockCode": code,
                "mktId": "ALL"  # 시장 구분 추가
            }
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()  # HTTP 에러 체크
            
            # 응답 로깅 추가
            self.logger.debug(f"Response content: {response.text[:200]}")  # 처음 200자만 로깅
            
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
    ) -> Dict:  # 반환 타입을 Dict로 변경
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
                "endDate": end_date,
                "share": "1",  # 주식 수 정보 포함
                "money": "1"   # 거래대금 정보 포함
            }
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # DataFrame으로 변환 후 다시 딕셔너리로 변환
            df = pd.DataFrame(data.get('output', []))
            return {"data": df.to_dict(orient='records')}
            
        except Exception as e:
            self.logger.error(f"Error fetching price history for {code}: {str(e)}")
            return {"data": []}

    def save_to_file(self, data: Dict, filename: str) -> None:
        """수집된 데이터를 파일로 저장"""
        try:
            save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'data', 'raw', f"{filename}.json")
            
            # DataFrame인 경우 처리
            if isinstance(data, pd.DataFrame):
                data = data.to_dict(orient='records')
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Successfully saved data to {filename}.json")
        except Exception as e:
            self.logger.error(f"Error saving data to file {filename}: {str(e)}")
