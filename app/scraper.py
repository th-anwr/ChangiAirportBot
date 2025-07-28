import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urljoin, urlparse
import time
import os

# --- New Imports for Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
START_URLS = [
    "https://www.changiairport.com/", 
    "https://www.jewelchangiairport.com/"
]

CRAWL_DEPTH = 3
CRAWL_DELAY = 4 # Increased delay slightly for browser rendering

EXCLUSION_KEYWORDS = ['login', 'signin', 'account', 'register', 'password']

# --- Global Variables ---
visited_urls = set()
collected_content = []

def is_valid_url(url, original_base_netloc):
    if not url:
        return False
    parsed_url = urlparse(url)
    if parsed_url.netloc != original_base_netloc:
        return False
    if parsed_url.scheme not in ("http", "https"):
        return False
    if '/zh/' in parsed_url.path.lower():
        return False
    if parsed_url.query:
        return False
    if any(keyword in parsed_url.path.lower() for keyword in EXCLUSION_KEYWORDS):
        return False
    return True

def get_links_from_html(soup, page_url, original_base_netloc):
    links = set()
    for anchor_tag in soup.find_all('a', href=True):
        absolute_link = urljoin(page_url, anchor_tag['href'])
        cleaned_link = absolute_link.split('#')[0]
        if is_valid_url(cleaned_link, original_base_netloc):
            links.add(cleaned_link)
    return links

def extract_text_from_html(html_content, url):
    extracted_text = trafilatura.extract(
        html_content, 
        url=url, 
        include_comments=False, 
        include_tables=False
    )
    if extracted_text and "Let’s give you the best experience possible" in extracted_text:
        print(f"-> Discarding cookie banner text from: {url}")
        return ""
    if extracted_text:
        return extracted_text.strip()
    print(f"-> Trafilatura failed for {url}, using basic text extraction.")
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove nav, footer, and script/style tags for fallback
    for tag in soup(['nav', 'footer', 'script', 'style']):
        tag.decompose()
    return ' '.join(soup.stripped_strings)

def crawl_website(driver, url, original_base_netloc, current_depth):
    if current_depth > CRAWL_DEPTH or url in visited_urls:
        return
    print(f"Crawling (Depth {current_depth}): {url}")
    visited_urls.add(url)
    try:
        driver.get(url)
        # Try to accept cookie banners if present
        try:
            driver.find_element(By.XPATH, "//button[contains(., 'Accept') or contains(., 'accept') or contains(., 'AGREE') or contains(., 'Agree')]").click()
            time.sleep(1)
        except Exception:
            pass
        # Wait for main content selector if possible
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "main, .main-content, #content"))
            )
        except Exception:
            print("-> Main content selector not found, continuing anyway.")
        time.sleep(CRAWL_DELAY)
        final_url = driver.current_url
        if final_url != url and urlparse(final_url).netloc == original_base_netloc:
            print(f"-> Redirected to: {final_url}")
            visited_urls.add(final_url)
        html = driver.page_source
        text = extract_text_from_html(html, final_url)
        if text:
            collected_content.append(f"URL: {final_url}\n\n{text}")
        else:
            print(f"-> No content extracted from: {final_url}")
            # Save HTML for debugging
            debug_path = f"debug_{urlparse(final_url).path.replace('/', '_')}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"-> Saved debug HTML to {debug_path}")
        if current_depth < CRAWL_DEPTH:
            soup = BeautifulSoup(html, 'html.parser')
            links_to_crawl = get_links_from_html(soup, final_url, original_base_netloc)
            print(f"--> Found {len(links_to_crawl)} valid links on page.")
            for link in links_to_crawl:
                crawl_website(driver, link, original_base_netloc, current_depth + 1)
    except WebDriverException as e:
        print(f"!! Selenium failed to crawl {url}: {e}")
    except Exception as e:
        print(f"!! An unexpected error occurred at {url}: {e}")

def main():
    print("Setting up Selenium WebDriver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        for start_url in START_URLS:
            original_base_netloc = urlparse(start_url).netloc
            print(f"\n--- Starting new crawl for base domain: {original_base_netloc} ---")
            crawl_website(driver, start_url, original_base_netloc, 0)
    finally:
        if driver:
            print("Closing Selenium WebDriver.")
            driver.quit()
    output_dir = "data"
    output_file = os.path.join(output_dir, "source_data.txt")
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nCrawling complete. Writing {len(collected_content)} pages to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in collected_content:
            f.write(entry + "\n\n" + "="*80 + "\n\n")
    print("Done.")

if __name__ == "__main__":
    main()
