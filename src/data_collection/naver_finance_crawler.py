import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

def get_driver():
    user_agent = UserAgent().random
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--dns-prefetch-disable")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver

def wait_for_element(driver, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except TimeoutException:
        print(f"Timed out waiting for element: {selector}")
        return None

def scrape_articles():
    base_url = "https://finance.naver.com"
    url = f"{base_url}/news/mainnews.naver"
    driver = get_driver()

    try:
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = []

        for item in soup.select(".articleSubject a"):
            title = item.get_text(strip=True)
            href = item["href"]
            link = href if href.startswith("http") else base_url + href

            for attempt in range(3):
                try:
                    driver.get(link)
                    time.sleep(random.uniform(2, 5))
                    break
                except WebDriverException as e:
                    print(f"Retrying to load {link} due to: {e}")
                    time.sleep(5)

            article_soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = article_soup.select_one('article#dic_area')

            if content_div:
                for tag in content_div(["script", "style"]):
                    tag.decompose()
                content = content_div.get_text(separator=" ", strip=True)
            else:
                content = "No content found"

            articles.append({"title": title, "link": link, "content": content})

        df = pd.DataFrame(articles)
        df.to_csv("data/raw/financial_news_full.csv", index=False)
        print("Data saved to data/raw/financial_news_full.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_articles()
