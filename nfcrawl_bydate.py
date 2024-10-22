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
from datetime import datetime, timedelta

def get_driver():
    user_agent = UserAgent().random
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver

def wait_for_element(driver, selector, timeout=15):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except TimeoutException:
        print(f"Timed out waiting for element: {selector}")
        return None

def generate_date_url(base_url, target_date):
    # Format the date in YYYYMMDD format
    date_str = target_date.strftime("%Y%m%d")
    return f"{base_url}/news/news_list.naver?date={date_str}"

def scrape_articles_for_date(target_date):
    base_url = "https://finance.naver.com"
    url = generate_date_url(base_url, target_date)
    driver = get_driver()

    try:
        driver.get(url)
        time.sleep(3)  # Allow the page to load initially

        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = []

        for item in soup.select(".articleSubject a"):
            title = item.get_text(strip=True)
            href = item["href"]

            if href.startswith("http"):
                link = href
            else:
                link = base_url + href

            print(f"Scraping Article: {title} - {link}")  # Debugging output

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
                content = content_div.get_text(separator=" ", strip=True)
            else:
                content = "No content found"
                print(f"No content found for: {title}")

            articles.append({"title": title, "link": link, "content": content})

        if articles:
            filename = f"financial_news_{target_date.strftime('%Y%m%d')}.csv"
            df = pd.DataFrame(articles)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        else:
            print(f"No articles found for {target_date.strftime('%Y-%m-%d')}.")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Example: Get data for 2024-10-21 and 2024-10-20, 2024-10-19, 2024-10-18...
    dates_to_scrape = [datetime(2024, 7, day) for day in range(1, 32)]
    for date in dates_to_scrape:
        scrape_articles_for_date(date)
