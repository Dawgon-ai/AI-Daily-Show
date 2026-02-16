import sys
import subprocess
import json
import datetime
from dateutil import parser as date_parser
import store_manager
import os

# Define Python Path
PYTHON_EXE = sys.executable

SOURCES = ["theverge", "techcrunch", "wired", "therundown"]

def run_scraper(source):
    # Added --sync flag to push directly to Supabase
    result = subprocess.run(
        [PYTHON_EXE, "tools/scraper.py", "--source", source, "--sync"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        sys.stderr.write(f"Error scraping {source}: {result.stderr}\n")
        return []
    
    try:
        # Since scraper prints only JSON to stdout (logs in stderr), we can parse directly
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error parsing JSON from {source}: {e}\n")
        return []

def is_recent(article):
    # For now, we assume scraped articles are 'new' because we don't strictly parse date in scraper yet.
    # But if we did:
    # pub_date = date_parser.parse(article["published_at"])
    # delta = datetime.datetime.now(datetime.timezone.utc) - pub_date
    # return delta.total_seconds() < 86400
    return True

def merge_articles(existing, new_scraped):
    url_map = {a["url"]: a for a in existing}
    
    count_new = 0
    for article in new_scraped:
        if article["url"] not in url_map:
            url_map[article["url"]] = article
            count_new += 1
        else:
            # Update existing if needed, but preserve 'is_saved'
            existing_article = url_map[article["url"]]
            # article['is_saved'] = existing_article.get('is_saved', False) # New scraped is always false
            # url_map[article["url"]] = article # Overwrite? Or keep old?
            pass # Keep old for now to preserve state

    return list(url_map.values()), count_new

def main():
    print("Starting Fetch Cycle...")
    
    # 1. Load Existing
    data = store_manager.load_data()
    existing_articles = data.get("articles", [])
    print(f"Loaded {len(existing_articles)} existing articles.")

    # 2. Scrape All
    all_new_scraped = []
    for source in SOURCES:
        print(f"Scraping {source}...")
        articles = run_scraper(source)
        print(f"Found {len(articles)} articles from {source}.")
        all_new_scraped.extend(articles)

    # 3. Merge
    updated_articles, new_count = merge_articles(existing_articles, all_new_scraped)
    print(f"Merged. {new_count} new articles added.")

    # 4. Filter (Prune old non-saved) - TODO: Implement strict 24h pruning when date parsing is robust.
    # For now, we just keep everything or limit to last 50? 
    # Let's limit to last 50 for sanity if list gets too big
    if len(updated_articles) > 50:
         # simple sort by date? they have 'published_at' string.
         updated_articles.sort(key=lambda x: x['published_at'], reverse=True)
         # Keep saved ones + top recent
         saved = [a for a in updated_articles if a.get('is_saved')]
         unsaved = [a for a in updated_articles if not a.get('is_saved')]
         updated_articles = saved + unsaved[:50]

    # 5. Save
    data["articles"] = updated_articles
    store_manager.save_data(data)
    print("Fetch Cycle Complete.")

if __name__ == "__main__":
    main()
