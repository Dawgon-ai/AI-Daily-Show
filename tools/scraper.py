import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
import datetime
import uuid
import re

# Configuration
SOURCES = {
    "theverge": {
        "url": "https://www.theverge.com/ai-artificial-intelligence",
        "base_url": "https://www.theverge.com"
    },
    "techcrunch": {
        "url": "https://techcrunch.com/category/artificial-intelligence/",
        "base_url": "https://techcrunch.com"
    },
    "wired": {
        "url": "https://www.wired.com/tag/artificial-intelligence/",
        "base_url": "https://www.wired.com"
    },
    "therundown": {
        "url": "https://www.therundown.ai/",
        "base_url": "https://www.therundown.ai"
    }
}

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

def fetch_articles(source_key):
    config = SOURCES.get(source_key)
    if not config:
        return []

    try:
        response = requests.get(config["url"], headers=get_headers(), timeout=10)
        response.raise_for_status()
    except Exception as e:
        sys.stderr.write(f"Error fetching {config['url']}: {e}\n")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    seen_urls = set()

    # --- Source Specific Parsing (Robust Fallbacks) ---
    parsed_items = [] # (element, source_specific_type)

    if source_key == "theverge":
        # Strategy 1: specific classes
        for h2 in soup.find_all("h2"): parsed_items.append(h2.find("a"))
        # Strategy 2: URL pattern
        if len(parsed_items) < 5:
            for a in soup.find_all("a", href=True):
                 if "/202" in a['href'] or "/ai-" in a['href']: parsed_items.append(a)

    elif source_key == "techcrunch":
        # Strategy 1: generic headings
        for h2 in soup.find_all("h2"): parsed_items.append(h2.find("a"))
        # Strategy 2: URL pattern
        if len(parsed_items) < 5:
             for a in soup.find_all("a", href=True):
                 if "/202" in a['href'] and len(a.get_text()) > 20: parsed_items.append(a)

    elif source_key == "wired":
        # Strategy 1: class search
        for div in soup.find_all(class_=re.compile("SummaryItem")): parsed_items.append(div.find("a"))
        # Strategy 2: Generic
        if len(parsed_items) < 5:
            for a in soup.find_all("a", href=True):
                if "/story/" in a['href']: parsed_items.append(a)

    elif source_key == "therundown":
        for a in soup.find_all('a', href=True):
            if "/p/" in a['href']: parsed_items.append(a)

    # --- Normalization Loop ---
    for item in parsed_items:
        if not item: continue
        try:
            a = item
            href = a['href']
            
            # Filter out non-article links/comments
            if "#" in href or "comment" in href or "author" in href: continue

            # Normalize URL
            if not href.startswith("http"):
                full_url = config["base_url"] + href
            else:
                full_url = href

            # Title
            title = a.get_text(strip=True)
            if not title or len(title) < 15: continue # Increased min length to avoid junk
            
            if full_url in seen_urls: continue
            seen_urls.add(full_url)
            
            # --- Generic Image Finder (Robust) ---
            image_url = None
            # 1. Look inside anchor
            img = a.find("img")
            if img: 
                image_url = img.get("src") or img.get("data-src")
            
            # 2. Look nearby (Parent's other children) if no image found yet
            if not image_url:
                parent = a.find_parent("div")
                if parent:
                    # Look for any image in this container
                    img = parent.find("img")
                    if img: image_url = img.get("src") or img.get("data-src")

            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": full_url,
                "source": source_key,
                "published_at": datetime.datetime.now().isoformat(),
                "summary": "",
                "is_saved": False,
                "image_url": image_url
            }
            articles.append(article)
        except Exception as e:
            continue

    # Quality Check: Sort by length of title? Or just return top results
    return articles[:20]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape AI newsletters")
    parser.add_argument("--source", required=True, help="Source key")
    args = parser.parse_args()

    results = fetch_articles(args.source)
    print(json.dumps(results, indent=2))
