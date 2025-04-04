import os
import json
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from duckduckgo_search import DDGS
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(filename="crawler.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Headers for web requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Get user's Documents folder for saving CSV
DOCUMENTS_FOLDER = os.path.join(os.path.expanduser("~"), "Documents")
CSV_FILE_PATH = os.path.join(DOCUMENTS_FOLDER, "Extracted_Links.csv")

# Ensure the directory exists
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

def crawl_website(url):
    """Extracts all links from a given website."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True)]
        
        return links if links else ["No links found"]
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return [f"Request failed: {e}"]

def scrape_page_content(url):
    """Scrapes the full content of a webpage."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        if len(response.text) < 1000:
            logging.warning(f"⚠️ Page might be JavaScript-rendered: {url}")
            return scrape_with_selenium(url)
        
        soup = BeautifulSoup(response.text, "html.parser")
        return extract_data(soup, url)
    except requests.RequestException as e:
        logging.error(f"❌ Error fetching {url}: {e}")
        return {"error": str(e)}

def scrape_with_selenium(url):
    """Scrapes JavaScript-rendered pages using Selenium."""
    logging.info(f"🌐 Using Selenium for {url}")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    return extract_data(soup, url)

def extract_data(soup, url="Unknown"):
    """Extracts structured data from a webpage."""
    headline = soup.find("title").text if soup.find("title") else "No Title Available"
    paragraphs = soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
    text_content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    
    if not text_content:
        text_content = soup.get_text().strip()[:5000]  # Fallback if structured content isn't found
    
    # Convert relative image URLs to absolute URLs
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            full_url = urljoin(url, src)  # Convert to absolute URL
            images.append(full_url)

    return {
        "url": url,
        "headline": headline,
        "text_content": text_content[:5000] if text_content else "No Content Extracted",
        "images": images[:5]  # Limit to 5 images
    }

def save_to_csv(data, filename=CSV_FILE_PATH):
    """Saves extracted links to a CSV file."""
    try:
        df = pd.DataFrame(data, columns=["URL"])
        df.to_csv(filename, index=False, encoding="utf-8")
        logging.info(f"✅ Data saved to {filename}")
    except Exception as e:
        logging.error(f"⚠️ Failed to save CSV: {e}")

def search_web(keyword, num_results=100):
    """Search DuckDuckGo for relevant links based on the keyword."""
    search_results = set()
    try:
        with DDGS() as ddgs:
            results = ddgs.text(keyword, max_results=num_results)
            for result in results:
                link = result.get("href", "")
                if link.startswith("http") and link not in search_results:
                    search_results.add(link)
    except Exception as e:
        logging.error(f"Error in DuckDuckGo search: {e}")
    return list(search_results)

@method_decorator(csrf_exempt, name='dispatch')
class SearchView(View):
    def get(self, request):
        """Fetch links for a keyword, display in chatbot, and save to CSV."""
        keyword = request.GET.get('keyword')
        if not keyword:
            return JsonResponse({"error": "Keyword is required"}, status=400)
        
        logging.info(f"🔍 Searching for: {keyword}")
        links = search_web(keyword, 100)
        if not links:
            return JsonResponse({"message": "No links found."})
        
        save_to_csv([[link] for link in links])
        return JsonResponse({"message": "✅ Links extracted successfully!", "links": links, "download_csv": "/download"})

class DownloadCSVView(View):
    def get(self, request):
        """Allow users to download the extracted links CSV file."""
        return FileResponse(open(CSV_FILE_PATH, "rb"), as_attachment=True)

class ScrapeView(View):
    def get(self, request):
        """Scrape content from a given URL and return structured data, including properly formatted images."""
        url = request.GET.get('url')
        if not url:
            return JsonResponse({"error": "URL is required"}, status=400)

        logging.info(f"🔍 Scraping content from: {url}")
        scraped_data = scrape_page_content(url)

        # Convert relative image URLs to absolute
        full_image_urls = [urljoin(url, img) for img in scraped_data["images"]]

        return JsonResponse({
            "url": scraped_data["url"],
            "headline": scraped_data["headline"],
            "text_content": scraped_data["text_content"][:1000],  # Limit text length for response
            "images": full_image_urls  # Return corrected image URLs
        })