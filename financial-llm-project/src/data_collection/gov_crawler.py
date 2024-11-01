import requests
import pandas as pd
import logging
from typing import Dict, List, Optional
import time
from random import uniform
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovDataCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.api_keys = self._load_api_keys()
        
    def _load_api_keys(self) -> Dict:
        """API 키를 로드합니다."""
        try:
            api_key_path = os.path.join('../../data/api_key', 'api_keys.json')
            with open(api_key_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("API 키 파일을 찾을 수 없습니다. data/api_key/api_keys.json 파일을 생성해주세요.")
            return {}
        except json.JSONDecodeError:
            logger.error("API 키 파일 형식이 잘못되었습니다.")
            return {}
            
    def safe_request(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[requests.Response]:
        """안전한 HTTP 요청을 수행합니다."""
        for i in range(max_retries):
            try:
                time.sleep(uniform(1, 3))
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                return response
            except Exception as e:
                logger.warning(f"요청 시도 {i+1}/{max_retries} 실패: {str(e)}")
                if i == max_retries - 1:
                    return None
                time.sleep(uniform(2, 5))
    
    def crawl_bok_data(self) -> List[Dict]:
        """한국은행 통계 API를 통해 데이터를 수집하고 의미있는 형태로 가공합니다."""
        logger.info("한국은행 데이터 수집 시작")
        data = []
        
        if 'BOK' not in self.api_keys:
            logger.error("한국은행 API 키가 설정되지 않았습니다.")
            return data
            
        # 통계표 목록을 가져옵니다
        list_url = f"https://ecos.bok.or.kr/api/StatisticTableList/{self.api_keys['BOK']}/json/kr/1/10"
        
        try:
            list_response = self.safe_request(list_url)
            if list_response and list_response.status_code == 200:
                json_data = list_response.json()
                if 'StatisticTableList' in json_data and 'row' in json_data['StatisticTableList']:
                    tables = json_data['StatisticTableList']['row']
                    logger.info(f"통계표 {len(tables)}개 발견")
                    
                    for table in tables:
                        stat_code = table.get('STAT_CODE')
                        if not stat_code:
                            continue
                        
                        current_date = datetime.now()
                        start_date = (current_date - timedelta(days=365)).strftime('%Y%m')
                        end_date = current_date.strftime('%Y%m')
                        
                        data_url = (
                            f"https://ecos.bok.or.kr/api/StatisticSearch/{self.api_keys['BOK']}"
                            f"/json/kr/1/100/{stat_code}/{table.get('CYCLE', 'M')}"
                            f"/{start_date}/{end_date}"
                        )
                        
                        data_response = self.safe_request(data_url)
                        if data_response and data_response.status_code == 200:
                            try:
                                stat_data = data_response.json()
                                if 'StatisticSearch' in stat_data and 'row' in stat_data['StatisticSearch']:
                                    items = stat_data['StatisticSearch']['row']
                                    for item in items:
                                        # 데이터를 더 의미있는 형태로 가공
                                        formatted_data = {
                                            'source': 'BOK',
                                            'category': '경제통계',
                                            'title': f"{table.get('STAT_NAME', '')} - {item.get('ITEM_NAME1', '')}",
                                            'date': self._format_date(item.get('TIME', '')),
                                            'content': (
                                                f"{item.get('ITEM_NAME1', '')}: "
                                                f"{item.get('DATA_VALUE', '')} {item.get('UNIT_NAME', '')}\n"
                                                f"통계 분류: {table.get('STAT_NAME', '')}\n"
                                                f"기준 시점: {self._format_date(item.get('TIME', ''))}"
                                            ),
                                            'raw_data': {
                                                'value': item.get('DATA_VALUE', ''),
                                                'unit': item.get('UNIT_NAME', ''),
                                                'stat_code': stat_code
                                            }
                                        }
                                        data.append(formatted_data)
                                    logger.info(f"통계표 {stat_code}에서 {len(items)}개 데이터 수집")
                            except Exception as e:
                                logger.error(f"통계 데이터 파싱 중 오류 발생 (코드: {stat_code}): {str(e)}")
                        
                        time.sleep(1)
        except Exception as e:
            logger.error(f"BOK API 호출 중 오류 발생: {str(e)}")
            
        return data

    def crawl_dart_data(self) -> List[Dict]:
        """DART API를 통해 공시 정보를 수집하고 상세 내용을 크롤링합니다."""
        logger.info("DART 데이터 수집 시작")
        data = []
        
        if 'DART' not in self.api_keys:
            logger.error("DART API 키가 설정되지 않았습니다.")
            return data
            
        base_url = 'https://opendart.fss.or.kr/api/list.json'
        
        try:
            params = {
                'crtfc_key': self.api_keys['DART'],
                'bgn_de': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                'end_de': datetime.now().strftime('%Y%m%d'),
                'page_no': 1,
                'page_count': 100
            }
            
            response = self.safe_request(base_url, params)
            if response and response.status_code == 200:
                json_data = response.json()
                disclosures = json_data.get('list', [])
                
                for disc in disclosures:
                    try:
                        # 공시 상세 정보 가져오기
                        rcept_no = disc.get('rcept_no', '')
                        corp_code = disc.get('corp_code', '')
                        
                        # 공시 원문 텍스트 가져오기 (HTML 형식으로 요청)
                        text_url = f"https://dart.fss.or.kr/report/viewer.do"
                        text_params = {
                            'rcpNo': rcept_no,
                            'dcmNo': '0',
                            'eleId': '0',
                            'offset': '0',
                            'length': '0',
                            'dtd': 'HTML'
                        }
                        
                        content = ""
                        # HTML 형식으로 공시 내용 요청
                        text_response = self.safe_request(text_url, text_params)
                        if text_response and text_response.status_code == 200:
                            soup = BeautifulSoup(text_response.content, 'html.parser')
                            # HTML에서 텍스트 추출
                            content = soup.get_text(separator='\n', strip=True)
                        
                        # 재무정보 요청 (있는 경우에만)
                        financial_data = {}
                        if '사업보고서' in disc.get('report_nm', ''):
                            financial_url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
                            financial_params = {
                                'crtfc_key': self.api_keys['DART'],
                                'corp_code': corp_code,
                                'bsns_year': datetime.now().year,
                                'reprt_code': '11011'
                            }
                            
                            financial_response = self.safe_request(financial_url, financial_params)
                            if financial_response and financial_response.status_code == 200:
                                financial_data = financial_response.json()
                        
                        # 데이터 통합
                        data.append({
                            'source': 'DART',
                            'category': '공시정보',
                            'corp_name': disc.get('corp_name', ''),
                            'title': disc.get('report_nm', '').strip(),
                            'date': disc.get('rcept_dt', ''),
                            'content': content[:1000] if content else "",  # 내용이 너무 길면 앞부분만 저장
                            'url': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
                            'raw_data': {
                                'corp_code': corp_code,
                                'stock_code': disc.get('stock_code', ''),
                                'disclosure_type': disc.get('report_nm', '').strip(),
                                'financial_data': financial_data
                            }
                        })
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"공시 상세정보 수집 중 오류 발생: {str(e)}")
                        
        except Exception as e:
            logger.error(f"DART API 호출 중 오류 발생: {str(e)}")
            
        return data

    def _format_date(self, date_str: str) -> str:
        """YYYYMM 형식의 날짜를 YYYY년 MM월 형식으로 변환합니다."""
        if len(date_str) == 6:
            return f"{date_str[:4]}년 {date_str[4:]}월"
        return date_str

    def crawl_all_data(self) -> List[Dict]:
        """모든 데이터를 수집합니다."""
        all_data = []
        
        # 각 API 데이터 수집
        bok_data = self.crawl_bok_data()
        dart_data = self.crawl_dart_data()
        
        # 데이터 통합
        all_data.extend(bok_data)
        all_data.extend(dart_data)
        
        # 결과 저장
        output_path = '../../data/raw/gov_data.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"총 {len(all_data)}개의 데이터 수집 완료")
        logger.info(f"- BOK: {len(bok_data)}개")
        logger.info(f"- DART: {len(dart_data)}개")
        
        return all_data

if __name__ == "__main__":
    crawler = GovDataCrawler()
    data = crawler.crawl_all_data()
    
