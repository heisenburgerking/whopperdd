from src.data_collection.naver_finance_crawler import scrape_articles
from src.data_collection.corp_code_downloader import download_corp_code
from api_key.key import naver_api_key

def main():
    # Step 1: Collect financial news articles
    scrape_articles()
    
    # Step 2: Download corporate codes
    API_KEY = naver_api_key
    OUTPUT_DIR = "data/raw"
    download_corp_code(API_KEY, OUTPUT_DIR)

if __name__ == "__main__":
    main()
