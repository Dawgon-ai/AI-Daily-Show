import json
import os
import sys
from datetime import datetime

DATA_FILE = "data/storage.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"last_updated": datetime.now().isoformat(), "articles": []}
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        sys.stderr.write(f"Error: {DATA_FILE} is corrupt. Starting fresh.\n")
        return {"last_updated": datetime.now().isoformat(), "articles": []}

def save_data(data):
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    data["last_updated"] = datetime.now().isoformat()
    
    try:
        # 1. Save JSON (Source of Truth for Backend)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
            
        # 2. Save JS (For Frontend - Bypass CORS)
        # Writes: window.DASHBOARD_DATA = { ... };
        js_path = os.path.join(os.path.dirname(DATA_FILE), "data.js")
        with open(js_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(data, indent=2)
            f.write(f"window.DASHBOARD_DATA = {json_str};")
            
        print(f"Data saved to {DATA_FILE} and {js_path}")
    except Exception as e:
        sys.stderr.write(f"Error saving data: {e}\n")

def get_articles():
    data = load_data()
    return data.get("articles", [])

def add_orphaned_articles(new_articles):
    # This function is intended to merge new articles
    # Logic is handled in fetch_articles.py usually, 
    # but specific manager helpers can go here.
    pass

if __name__ == "__main__":
    # Test
    data = load_data()
    print(f"Loaded {len(data.get('articles', []))} articles.")
