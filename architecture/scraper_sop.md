# Scraper SOP (scraper_sop.md)

## Purpose
To deterministically fetch article metadata (title, url, date) from target newsletter sources using `tools/scraper.py`.

## Tool Config: `tools/scraper.py`

### Usage
```bash
python tools/scraper.py --source <source_key>
```

### Source Keys
- `bensbites`: `https://bensbites.com/archive`
- `therundown`: `https://www.therundown.ai/`

### Logic
1.  **Fetch**: HTTP GET the target URL.
2.  **Parse**: Use BeautifulSoup to parse HTML.
3.  **Extract**: Find all `<a>` tags.
    - **Ben's Bites**: Look for `href` containing `/p/`. Title is text. Date is inferred or skipped for now.
    - **The Rundown**: Look for `href` containing `/p/`. Title is text.
4.  **Format**: Return a JSON list of objects matching the `Article` schema in `gemini.md`.
5.  **Output**: Print JSON to stdout.

### Error Handling
- If connection fails: Return empty list `[]` and log error to stderr.
- If parsing fails: Return partial list.
