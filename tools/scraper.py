import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
import datetime
import uuid
import re
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

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

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = None

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

def generate_ai_image(title, source):
    # Ensure title is safe for URL
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    query = f"{clean_title} AI Tech {source}".replace(" ", "%20")
    # Pollinations.ai allows dynamic image generation via URL
    return f"https://image.pollinations.ai/prompt/{query}?width=1024&height=1024&nologo=true&enhance=true"

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
        # Strategy 1: Look for article containers
        containers = soup.find_all("div", class_="duet--content-cards--content-card")
        if not containers:
            # Fallback
            for h2 in soup.find_all("h2"): parsed_items.append((h2, "heading"))
        else:
            for c in containers: parsed_items.append((c, "container"))

    elif source_key == "techcrunch":
        # Strategy: Look for loop-item containers
        containers = soup.find_all("div", class_="wp-block-post") or soup.find_all("li", class_="wp-block-post")
        if not containers:
            for h2 in soup.find_all("h2"): parsed_items.append((h2, "heading"))
        else:
            for c in containers: parsed_items.append((c, "container"))

    elif source_key == "wired":
        # Strategy: SummaryItem class
        containers = soup.find_all(class_=re.compile("SummaryItem"))
        for c in containers: parsed_items.append((c, "container"))

    elif source_key == "therundown":
        for a in soup.find_all('a', href=True):
            if "/p/" in a['href']: parsed_items.append((a, "link"))

    # --- Normalization Loop ---
    for element, el_type in parsed_items:
        if not element: continue
        try:
            # Find the anchor tag
            a = element if el_type == "link" else element.find("a", href=True)
            if not a: continue
            
            href = a['href']
            # Filter out non-article links
            if any(x in href for x in ["#", "comment", "author", "/category/", "/tags/"]): continue

            # Normalize URL
            full_url = href if href.startswith("http") else config["base_url"] + href
            if full_url in seen_urls: continue
            seen_urls.add(full_url)

            # Title extraction based on element type
            title = ""
            if el_type == "container":
                t_el = element.find(["h2", "h3"])
                title = t_el.get_text(strip=True) if t_el else a.get_text(strip=True)
            else:
                title = a.get_text(strip=True)
            
            if not title or len(title) < 15: continue

            # --- Robust Image Finder ---
            image_url = None
            
            # 1. Look for images in the container/element
            img = element.find("img")
            if img:
                # Check different attributes for lazy-loaded images
                image_url = img.get("src") or img.get("data-src") or img.get("srcset", "").split(" ")[0]
            
            # 2. TechCrunch specific meta/fallback
            if not image_url and source_key == "techcrunch":
                figure = element.find("figure")
                if figure:
                    img = figure.find("img")
                    if img: 
                        image_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                
                # TechCrunch sometimes has images in a different container structure
                if not image_url:
                    img_container = element.find("div", class_="wp-block-post-featured-image")
                    if img_container:
                        img = img_container.find("img")
                        if img: image_url = img.get("src") or img.get("data-src")

            # 3. AI GENERATION FALLBACK
            if not image_url:
                image_url = generate_ai_image(title, source_key)
            
            # Build the article object
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

    return articles[:20]

def sync_to_supabase(articles):
    if not supabase:
        sys.stderr.write("Supabase client not initialized. Skipping sync.\n")
        return

    # Prepare historical match check (to avoid overwriting image_urls if we already have one)
    for article in articles:
        try:
            # Upsert into articles table
            # We use 'ON CONFLICT (url) DO UPDATE' logic via supabase select/insert if needed
            # But the 'url' is unique, so we can check existence
            
            # Simple Upsert
            data = {
                "title": article["title"],
                "url": article["url"],
                "source": article["source"],
                "published_at": article["published_at"],
                "image_url": article["image_url"],
                "summary": article["summary"]
            }
            
            # Using upsert with the unique constraint on 'url'
            # Note: For this to work well, we need to ensure the DB knows 'url' is the conflict target
            # In Supabase UI/SQL: ALTER TABLE articles ADD CONSTRAINT articles_url_key UNIQUE (url);
            supabase.table("articles").upsert(data, on_conflict="url").execute()
            
        except Exception as e:
            sys.stderr.write(f"Error syncing to Supabase: {e}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape AI newsletters")
    parser.add_argument("--source", required=True, help="Source key")
    parser.add_argument("--sync", action="store_true", help="Sync to Supabase")
    args = parser.parse_args()

    # All logs to stderr to keep stdout clean for JSON
    sys.stderr.write(f"Scraping {args.source}...\n")
    results = fetch_articles(args.source)
    
    if args.sync:
        sys.stderr.write(f"Syncing {len(results)} articles from {args.source} to Supabase...\n")
        sync_to_supabase(results)
    
    # Still print results for piping if needed - this MUST be the only thing on stdout
    print(json.dumps(results, indent=2))
