from urllib import request
from zipfile import ZipFile
import ssl
import os
from api_key.key import keys

def download_corp_code(api_key, output_dir):
    context = ssl._create_unverified_context()
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    print("요청주소 : " + url)

    data = request.urlopen(url, context=context)
    filename = data.info().get_filename()
    print("파일명 : " + filename)

    with open(filename, 'wb') as f:
        f.write(data.read())

    print("다운로드 완료.")

    with ZipFile(filename, 'r') as zipObj:
        zipObj.extractall(output_dir)

    if os.path.isfile(filename):
        os.remove(filename)

if __name__ == "__main__":
    API_KEY = keys["naver_api_key"]
    OUTPUT_DIR = "data/raw"
    download_corp_code(API_KEY, OUTPUT_DIR)
