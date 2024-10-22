from urllib import request
from zipfile import ZipFile
import ssl, os
	
context = ssl._create_unverified_context()

API_KEY="a7e56986db917ef1cd849184b6a8560a179b299f"
url = "https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key="+API_KEY
print("요청주소 : " + url)

data = request.urlopen(url, context=context)
filename = data.info().get_filename()
print("파일명 : " + filename)

with open(filename, 'wb') as f:
    f.write(data.read())
    f.close

print("다운로드 완료.")

with ZipFile(filename, 'r') as zipObj:
   zipObj.extractall('./') # 현재 디렉토리에 압축을 해제

if os.path.isfile(filename):
  os.remove(filename) # 원본 압축파일 삭제