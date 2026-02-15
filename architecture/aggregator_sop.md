# Aggregator SOP (aggregator_sop.md)

## Purpose
To orchestrate the collection, filtering, and storage of articles from multiple sources.

## Logic Flow
1.  **Orchestrator (`fetch_articles.py`)** initiates the process.
2.  **Scrape**: Call `scraper.py` for each source in `SOURCES`.
3.  **Load**: Load existing data from `data/storage.json` via `store_manager.py`.
4.  **Filter**:
    - **Time**: Discard articles older than 24 hours (unless they are already saved).
    - **Deduplication**: Check if URL already exists in storage.
5.  **Merge**: Add new unique articles to the list.
6.  **Prune**: Remove non-saved articles older than 24 hours.
7.  **Save**: Write updated list back to `data/storage.json`.

## Data Structure
The `storage.json` file adheres to the `Dashboard State` schema in `gemini.md`.

## Error Handling
- Partial Failures: If one source fails, others must continue.
- Corrupt Storage: If JSON is invalid, backup and start fresh (Self-Healing).
