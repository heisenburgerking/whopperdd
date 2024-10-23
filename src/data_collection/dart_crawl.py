import requests
import xml.etree.ElementTree as ET

# Open DART API 키 (https://opendart.fss.or.kr/ 에서 발급받으세요)
api_key = 'YOUR_API_KEY'

# 기업 코드 조회 함수
def get_corp_code(corp_name):
    url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}'
    response = requests.get(url)
    with open('corpCode.xml', 'wb') as f:
        f.write(response.content)
    tree = ET.parse('corpCode.xml')
    root = tree.getroot()
    for list in root.findall('list'):
        if list.find('corp_name').text == corp_name:
            return list.find('corp_code').text
    return None

# 재무제표 조회 함수
def get_financial_statements(corp_code, bsns_year, reprt_code='11011'):
    url = f'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
    params = {
        'crtfc_key': api_key,
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

# 사용 예시
corp_name = '삼성전자'
corp_code = get_corp_code(corp_name)
if corp_code:
    data = get_financial_statements(corp_code, '2022')
    print(data)
else:
    print('해당 기업을 찾을 수 없습니다.')
