# Project Constitution (gemini.md)

## Data Schemas

### Article
```json
{
  "id": "string (uuid)",
  "title": "string",
  "url": "string",
  "source": "string (e.g., 'Bens Bites', 'AI Rundown')",
  "published_at": "datetime (ISO 8601)",
  "summary": "string",
  "content": "string (optional)",
  "is_saved": "boolean"
}
```

### Source
```json
{
  "name": "string",
  "url": "string",
  "type": "newsletter|rss|web",
  "scraper_config": "object"
}
```

### Dashboard State
```json
{
  "last_updated": "datetime",
  "articles": "Array<Article>",
  "saved_articles": "Array<string> (Article IDs)"
}
```

## Behavioral Rules
1.  **Aesthetics**: Design must be gorgeous, interactive, and premium. Use rich colors, micro-animations, and glassmorphism.
2.  **Data Currency**: Only display articles from the last 24 hours (unless saved).
3.  **Persistence**: Saved articles must persist across refreshes.
4.  **Source of Truth**: Initially, data exists within the website (local JSON/Storage). move to Supabase later.
5.  **Frequency**: Automated run every 24 hours.

## Architectural Invariants
1. **Data-First Rule**: Define schemata before coding.
2. **Self-Healing**: Analyze -> Patch -> Test -> Update Architecture.
3. **3-Layer Architecture**: Architecture (SOPs) -> Navigation (Logic) -> Tools (Scripts).

## Maintenance Log

### How to Run
1.  **Start Dashboard**: Open `index.html` in your browser.
2.  **Start Automation**: Run `python tools/run_loop.py` in a terminal. Keep this window open.

### Troubleshooting
-   **Scrapers Failing**: Check `architecture/scraper_sop.md` and update `tools/scraper.py` selectors if source websites change.
-   **Data Corrupt**: Delete `data/storage.json` to reset (Self-Healing will create a new one).

### Future Roadmap
-   Transition `data/storage.json` to Supabase.
-   Add more sources (Reddit, Twitter).
-   Deploy Frontend to Vercel/Netlify.

