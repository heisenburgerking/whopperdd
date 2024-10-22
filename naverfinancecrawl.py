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

# Step 1: Configure Selenium WebDriver with User-Agent rotation
def get_driver():
    user_agent = UserAgent().random  # Random User-Agent to avoid detection
    chrome_options = Options()

    # Browser configuration
    chrome_options.add_argument(f"user-agent={user_agent}")
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--dns-prefetch-disable")  # Optional DNS optimization

    # Initialize WebDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver

# Step 2: Wait for elements with retries
def wait_for_element(driver, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except TimeoutException:
        print(f"Timed out waiting for element: {selector}")
        return None

# Step 3: Scrape the main page for article links and headlines
def scrape_articles():
    base_url = "https://finance.naver.com"
    url = f"{base_url}/news/mainnews.naver"
    driver = get_driver()

    try:
        driver.get(url)
        time.sleep(3)  # Allow the page to load initially

        # Parse the main page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = []

        # Extract article links
        for item in soup.select(".articleSubject a"):
            title = item.get_text(strip=True)
            href = item["href"]

            # Ensure proper URL construction
            if href.startswith("http"):
                link = href
            else:
                link = base_url + href

            # Navigate to the article page with retries
            for attempt in range(3):
                try:
                    driver.get(link)
                    time.sleep(random.uniform(2, 5))  # Random delay to avoid detection
                    break
                except WebDriverException as e:
                    print(f"Retrying to load {link} due to: {e}")
                    time.sleep(5)
            # Print page source to inspect the HTML structure
            print(driver.page_source)

            # Parse the article page
            article_soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = article_soup.select_one('article#dic_area')

            # Extract article content
            if content_div:
                # Remove unwanted tags (e.g., <script>, <style>)
                for tag in content_div(["script", "style"]):
                    tag.decompose()

                content = content_div.get_text(separator=" ", strip=True)
            else:
                content = "No content found"

            # Save the data
            articles.append({"title": title, "link": link, "content": content})

        # Save to CSV
        df = pd.DataFrame(articles)
        df.to_csv("financial_news_full.csv", index=False)
        print("Data saved to financial_news_full.csv")

    finally:
        # Ensure the driver quits even on error
        driver.quit()

# Run the script
if __name__ == "__main__":
    scrape_articles()
