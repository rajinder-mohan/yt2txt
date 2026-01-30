# MrBallen Channel Scraper

This script processes videos from the "MrBallen" channel by:
1. Fetching video IDs from the database
2. Downloading audio using yt-dlp
3. Scraping additional data using Selenium
4. Storing data back into the database

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Install ChromeDriver:**
   - Download from https://chromedriver.chromium.org/
   - Or use: `pip install webdriver-manager` (alternative)
   - Set `CHROMEDRIVER_PATH` environment variable if not in PATH

3. **Configure environment variables:**
   Create a `.env` file in the project root with:
   ```bash
   # Database configuration
   DB_TYPE=sqlite  # or postgres
   SQLITE_PATH=youtube_transcriptions.db
   
   # PostgreSQL (if DB_TYPE=postgres)
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=youtube_transcriptions
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   
   # Optional: ChromeDriver path
   CHROMEDRIVER_PATH=/path/to/chromedriver
   ```

4. **Ensure cookies.txt exists:**
   Place `cookies.txt` in the root directory for yt-dlp authentication.

## Usage

Run the script:
```bash
python scripts/mrballen_scraper.py
```

## Captcha Handling

If a captcha appears:
1. The script will detect it and pause
2. Solve the captcha in the browser window
3. Come back to the terminal and press ENTER
4. The script will continue processing

## Output

- Audio files are saved to `scripts/audio_downloads/`
- Logs are written to `scripts/mrballen_scraper.log`
- Video data is updated in the database

## Notes

- The script runs separately from the main application (no Docker)
- It processes videos one at a time with delays to avoid rate limiting
- Make sure the database has videos for "MrBallen" channel before running
