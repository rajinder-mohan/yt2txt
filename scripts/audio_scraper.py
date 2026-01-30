#!/usr/bin/env python3
"""
MrBallen Channel Scraper
========================
This script:
1. Connects to database using environment variables
2. Fetches video IDs for "MrBallen" channel
3. Downloads audio using yt-dlp
4. Scrapes additional data using Selenium
5. Stores data into database

Handles captcha by waiting for user to press Enter in console.
"""

import os
import sys
import time
import json
import re
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/mrballen_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database configuration from environment
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
SQLITE_PATH = os.getenv("SQLITE_PATH", "youtube_transcriptions.db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "youtube_transcriptions")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Channel name
CHANNEL_NAME = "MrBallen"

# Audio download directory
AUDIO_DIR = Path("scripts/audio_downloads")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    """Get database connection based on DB_TYPE."""
    if DB_TYPE == "postgres":
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=10
            )
            return conn
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgreSQL. Install: pip install psycopg2-binary")
    else:  # SQLite
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def fetch_mrballen_videos() -> List[Dict]:
    """Fetch video IDs for MrBallen channel from database."""
    conn = get_db_connection()
    videos = []
    
    try:
        if DB_TYPE == "postgres":
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT video_id, video_url, status, title, duration, view_count, 
                       upload_date, channel_name, channel_id, metadata
                FROM video_transcriptions
                WHERE channel_name = %s
                  AND (audio_file_path IS NULL OR audio_file_path = '')
                ORDER BY created_at DESC
                LIMIT 2
            """, (CHANNEL_NAME,))
            rows = cursor.fetchall()
            cursor.close()
        else:  # SQLite
            cursor = conn.cursor()
            cursor.execute("""
                SELECT video_id, video_url, status, title, duration, view_count, 
                       upload_date, channel_name, channel_id, metadata
                FROM video_transcriptions
                WHERE channel_name = ?
                  AND (audio_file_path IS NULL OR audio_file_path = '')
                ORDER BY created_at DESC
                LIMIT 2
            """, (CHANNEL_NAME,))
            rows = cursor.fetchall()
            cursor.close()
        
        for row in rows:
            if DB_TYPE == "postgres":
                videos.append(dict(row))
            else:  # SQLite
                videos.append({
                    'video_id': row['video_id'],
                    'video_url': row['video_url'],
                    'status': row['status'],
                    'title': row['title'],
                    'duration': row['duration'],
                    'view_count': row['view_count'],
                    'upload_date': row['upload_date'],
                    'channel_name': row['channel_name'],
                    'channel_id': row['channel_id'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None
                })
        
        logger.info(f"Found {len(videos)} videos for {CHANNEL_NAME} channel")
        return videos
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return []
    finally:
        conn.close()


def wait_for_captcha_solve():
    """Wait for user to solve captcha and press Enter."""
    logger.warning("=" * 60)
    logger.warning("CAPTCHA DETECTED!")
    logger.warning("Please solve the captcha in the browser window.")
    logger.warning("After solving, come back here and press ENTER to continue...")
    logger.warning("=" * 60)
    input("Press ENTER after solving captcha: ")
    logger.info("Continuing after captcha solve...")


def check_for_captcha(driver):
    """Check if captcha is present on the page."""
    try:
        # Common captcha indicators
        captcha_indicators = [
            "captcha",
            "verify you're not a robot",
            "i'm not a robot",
            "recaptcha",
            "hcaptcha"
        ]
        
        page_text = driver.page_source.lower()
        for indicator in captcha_indicators:
            if indicator in page_text:
                return True
        
        # Check for common captcha elements
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            ".g-recaptcha",
            "#captcha",
            "[data-callback*='captcha']"
        ]
        
        for selector in captcha_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        
        return False
    except Exception as e:
        logger.debug(f"Error checking for captcha: {e}")
        return False


def get_selenium_driver():
    """Initialize and return Selenium WebDriver."""
    chrome_options = Options()
    
    # Common Chrome options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Enable performance logging to capture network requests (optional)
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # User agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Optional: Run headless (set to False to see browser)
    # chrome_options.add_argument('--headless')
    
    # Try to find ChromeDriver
    # You can set CHROMEDRIVER_PATH environment variable
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        logger.info("Selenium WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize ChromeDriver: {e}")
        logger.error("Make sure ChromeDriver is installed and in PATH, or set CHROMEDRIVER_PATH env var")
        raise


def scrape_video_data_selenium(driver, video_url: str) -> Dict:
    """Scrape additional video data using Selenium."""
    logger.info(f"Scraping video data with Selenium: {video_url}")
    
    data = {
        'title': None,
        'description': None,
        'view_count': None,
        'like_count': None,
        'comment_count': None,
        'upload_date': None,
        'duration': None,
        'tags': []
    }
    
    try:
        driver.get(video_url)
        time.sleep(3)  # Wait for page to load
        
        # Check for captcha
        if check_for_captcha(driver):
            wait_for_captcha_solve()
            time.sleep(2)
        
        # Try to get title
        try:
            title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata yt-formatted-string, h1.ytd-video-primary-info-renderer, h1 yt-formatted-string"))
            )
            data['title'] = title_element.text.strip()
        except TimeoutException:
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, "h1.ytd-watch-metadata, h1")
                data['title'] = title_element.text.strip()
            except NoSuchElementException:
                logger.warning("Could not find title")
        
        # Try to get view count
        try:
            view_element = driver.find_element(By.CSS_SELECTOR, "span.view-count, .view-count, #count span")
            view_text = view_element.text.strip()
            # Extract number from text like "1.2M views" or "1,234,567 views"
            import re
            numbers = re.findall(r'[\d.]+', view_text.replace(',', ''))
            if numbers:
                view_str = numbers[0]
                if 'K' in view_text.upper():
                    data['view_count'] = int(float(view_str) * 1000)
                elif 'M' in view_text.upper():
                    data['view_count'] = int(float(view_str) * 1000000)
                elif 'B' in view_text.upper():
                    data['view_count'] = int(float(view_str) * 1000000000)
                else:
                    data['view_count'] = int(float(view_str))
        except (NoSuchElementException, ValueError) as e:
            logger.debug(f"Could not extract view count: {e}")
        
        # Try to get description
        try:
            # Click "Show more" if present
            try:
                show_more = driver.find_element(By.CSS_SELECTOR, "tp-yt-paper-button#expand, button[aria-label*='more'], .more-button")
                if show_more.is_displayed():
                    show_more.click()
                    time.sleep(1)
            except NoSuchElementException:
                pass
            
            desc_element = driver.find_element(By.CSS_SELECTOR, "#description, ytd-video-secondary-info-renderer #description, .ytd-video-secondary-info-renderer")
            data['description'] = desc_element.text.strip()
        except NoSuchElementException:
            logger.debug("Could not find description")
        
        # Try to get like count
        try:
            like_element = driver.find_element(By.CSS_SELECTOR, "yt-formatted-string#text.ytd-toggle-button-renderer, button[aria-label*='like'] span, #top-level-buttons yt-formatted-string")
            like_text = like_element.text.strip()
            import re
            numbers = re.findall(r'[\d.]+', like_text.replace(',', ''))
            if numbers:
                like_str = numbers[0]
                if 'K' in like_text.upper():
                    data['like_count'] = int(float(like_str) * 1000)
                elif 'M' in like_text.upper():
                    data['like_count'] = int(float(like_str) * 1000000)
                else:
                    data['like_count'] = int(float(like_str))
        except (NoSuchElementException, ValueError) as e:
            logger.debug(f"Could not extract like count: {e}")
        
        logger.info(f"Scraped data: title={data['title'][:50] if data['title'] else None}, views={data['view_count']}")
        
    except Exception as e:
        logger.error(f"Error scraping video data with Selenium: {e}")
    
    return data


def extract_video_stream_url(driver, video_url: str) -> Optional[str]:
    """Extract video/audio stream URL from YouTube page using Selenium."""
    logger.info(f"Extracting stream URL from: {video_url}")
    
    try:
        driver.get(video_url)
        time.sleep(5)  # Wait for page to fully load
        
        # Check for captcha
        if check_for_captcha(driver):
            wait_for_captcha_solve()
            time.sleep(3)
        
        # Wait for video player to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video, #movie_player"))
            )
        except TimeoutException:
            logger.warning("Video player not found, trying to extract from page source")
        
        # Method 1: Try to get stream URL from page source/JavaScript
        page_source = driver.page_source
        
        # Look for ytInitialPlayerResponse in page source
        match = re.search(r'var ytInitialPlayerResponse = ({.+?});', page_source, re.DOTALL)
        if not match:
            # Try alternative pattern
            match = re.search(r'"ytInitialPlayerResponse":({.+?})', page_source, re.DOTALL)
        
        if match:
            try:
                player_response = json.loads(match.group(1))
                
                # Extract streaming data
                streaming_data = player_response.get('streamingData', {})
                formats = streaming_data.get('formats', [])
                adaptive_formats = streaming_data.get('adaptiveFormats', [])
                
                # Combine all formats
                all_formats = formats + adaptive_formats
                
                # Find best audio format (prefer audio-only, then highest quality)
                audio_formats = [f for f in all_formats if f.get('mimeType', '').startswith('audio/')]
                
                if audio_formats:
                    # Sort by bitrate (quality)
                    audio_formats.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                    best_audio = audio_formats[0]
                    
                    # Get the URL
                    stream_url = best_audio.get('url') or best_audio.get('signatureCipher')
                    
                    if stream_url:
                        # If it's signatureCipher, we need to decode it
                        if 'signatureCipher' in best_audio:
                            # Extract URL from signatureCipher
                            cipher_match = re.search(r'url=([^&]+)', best_audio['signatureCipher'])
                            if cipher_match:
                                import urllib.parse
                                stream_url = urllib.parse.unquote(cipher_match.group(1))
                        
                        logger.info(f"Found audio stream URL (format: {best_audio.get('mimeType', 'unknown')})")
                        return stream_url
                
                # Fallback: get any video format and extract audio later
                if all_formats:
                    all_formats.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                    best_format = all_formats[0]
                    stream_url = best_format.get('url') or best_format.get('signatureCipher')
                    
                    if stream_url and 'signatureCipher' in best_format:
                        cipher_match = re.search(r'url=([^&]+)', best_format['signatureCipher'])
                        if cipher_match:
                            import urllib.parse
                            stream_url = urllib.parse.unquote(cipher_match.group(1))
                    
                    if stream_url:
                        logger.info(f"Found video stream URL (will extract audio)")
                        return stream_url
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse player response: {e}")
        
        # Method 2: Try to intercept network requests (if enabled)
        # This would require enabling network logging in Chrome options
        
        logger.warning("Could not extract stream URL from page")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting stream URL: {e}")
        return None


def download_audio_from_url(video_id: str, stream_url: str) -> Optional[str]:
    """Download audio from stream URL using requests."""
    logger.info(f"Downloading audio from stream URL for video: {video_id}")
    
    output_file = AUDIO_DIR / f"{video_id}.mp3"
    
    try:
        # Set up session with cookies if available
        session = requests.Session()
        
        # Load cookies from cookies.txt if exists
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            try:
                # Parse Netscape cookie format
                cookies_dict = {}
                with open(cookies_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('HttpOnly'):
                            parts = line.split('\t')
                            if len(parts) >= 7:
                                domain = parts[0]
                                name = parts[5]
                                value = parts[6]
                                if 'youtube.com' in domain or 'google.com' in domain:
                                    cookies_dict[name] = value
                
                # Set cookies for youtube.com domain
                for name, value in cookies_dict.items():
                    session.cookies.set(name, value, domain='.youtube.com')
                
                logger.info(f"Loaded {len(cookies_dict)} cookies from cookies.txt")
            except Exception as e:
                logger.warning(f"Could not load cookies: {e}")
        
        # Set headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        }
        
        # Download the stream
        logger.info("Starting download...")
        response = session.get(stream_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check if it's audio or video
        content_type = response.headers.get('Content-Type', '')
        is_audio = 'audio' in content_type.lower()
        
        # Download to temporary file first
        temp_file = AUDIO_DIR / f"{video_id}_temp.{'mp3' if is_audio else 'mp4'}"
        
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if int(percent) % 10 == 0:  # Log every 10%
                            logger.info(f"Downloaded: {percent:.1f}%")
        
        logger.info(f"Downloaded {downloaded / (1024*1024):.2f} MB")
        
        # If it's video, we need to extract audio (requires ffmpeg)
        if not is_audio:
            logger.info("Extracting audio from video (requires ffmpeg)...")
            import subprocess
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("ffmpeg not found. Cannot extract audio from video stream.")
                logger.error("Please install ffmpeg or use an audio-only stream URL")
                temp_file.unlink()  # Delete temp file
                return None
            
            # Extract audio using ffmpeg
            try:
                subprocess.run([
                    'ffmpeg', '-i', str(temp_file),
                    '-vn', '-acodec', 'libmp3lame', '-ab', '192k',
                    '-ar', '44100', '-y', str(output_file)
                ], check=True, capture_output=True)
                
                # Delete temp video file
                temp_file.unlink()
                logger.info(f"Audio extracted: {output_file}")
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg extraction failed: {e}")
                temp_file.unlink()
                return None
        else:
            # It's already audio, just rename
            temp_file.rename(output_file)
            logger.info(f"Audio file saved: {output_file}")
        
        if output_file.exists():
            file_size = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"Audio downloaded successfully: {output_file} ({file_size:.2f} MB)")
            return str(output_file)
        else:
            logger.error("Audio file not found after download")
            return None
            
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        return None


def download_audio(video_id: str, video_url: str, driver) -> Optional[str]:
    """Download audio for a video using Selenium to extract stream URL."""
    logger.info(f"Downloading audio for video: {video_id}")
    
    # Extract stream URL using Selenium
    stream_url = extract_video_stream_url(driver, video_url)
    
    if not stream_url:
        logger.error("Could not extract stream URL")
        return None
    
    # Download audio from stream URL
    audio_file = download_audio_from_url(video_id, stream_url)
    
    return audio_file


def update_video_in_db(video_id: str, selenium_data: Dict, audio_file_path: Optional[str] = None):
    """Update video record in database with scraped data."""
    conn = get_db_connection()
    
    try:
        # Get existing metadata first
        existing_metadata = {}
        if DB_TYPE == "postgres":
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT metadata FROM video_transcriptions WHERE video_id = %s", (video_id,))
            row = cursor.fetchone()
            cursor.close()
            if row and row['metadata']:
                existing_metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata FROM video_transcriptions WHERE video_id = ?", (video_id,))
            row = cursor.fetchone()
            cursor.close()
            if row and row[0]:
                existing_metadata = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        
        # Update metadata with new data
        if selenium_data.get('description'):
            existing_metadata['description'] = selenium_data['description']
        if selenium_data.get('like_count'):
            existing_metadata['like_count'] = selenium_data['like_count']
        
        # Prepare update data
        update_fields = []
        update_values = []
        
        if selenium_data.get('title'):
            update_fields.append("title = ?" if DB_TYPE == "sqlite" else "title = %s")
            update_values.append(selenium_data['title'])
        
        if selenium_data.get('view_count'):
            update_fields.append("view_count = ?" if DB_TYPE == "sqlite" else "view_count = %s")
            update_values.append(selenium_data['view_count'])
        
        if existing_metadata:
            metadata_json = json.dumps(existing_metadata)
            update_fields.append("metadata = ?" if DB_TYPE == "sqlite" else "metadata = %s::jsonb")
            update_values.append(metadata_json)
        
        if audio_file_path:
            update_fields.append("audio_file_path = ?" if DB_TYPE == "sqlite" else "audio_file_path = %s")
            update_values.append(audio_file_path)
            update_fields.append("status = ?" if DB_TYPE == "sqlite" else "status = %s")
            update_values.append("processed")
        
        update_fields.append("updated_at = ?" if DB_TYPE == "sqlite" else "updated_at = %s")
        update_values.append(datetime.now())
        
        update_values.append(video_id)  # For WHERE clause
        
        if update_fields:
            query = f"""
                UPDATE video_transcriptions 
                SET {', '.join(update_fields)}
                WHERE video_id = {'?' if DB_TYPE == 'sqlite' else '%s'}
            """
            
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute(query, tuple(update_values))
                conn.commit()
                cursor.close()
            else:
                cursor = conn.cursor()
                cursor.execute(query, tuple(update_values))
                conn.commit()
                cursor.close()
            
            logger.info(f"Updated video {video_id} in database")
    except Exception as e:
        logger.error(f"Error updating video in database: {e}")
        if DB_TYPE == "postgres":
            conn.rollback()
    finally:
        conn.close()


def process_video(video: Dict, driver):
    """Process a single video: download audio and scrape data."""
    video_id = video['video_id']
    video_url = video.get('video_url') or f"https://www.youtube.com/watch?v={video_id}"
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing video: {video_id}")
    logger.info(f"URL: {video_url}")
    logger.info(f"{'='*60}\n")
    
    # Scrape data with Selenium first (page is already loaded)
    selenium_data = scrape_video_data_selenium(driver, video_url)
    
    # Download audio using Selenium to extract stream URL
    audio_file_path = download_audio(video_id, video_url, driver)
    
    # Update database
    update_video_in_db(video_id, selenium_data, audio_file_path)
    
    logger.info(f"Completed processing video: {video_id}\n")


def main():
    """Main function to run the scraper."""
    logger.info("=" * 60)
    logger.info("MrBallen Channel Scraper")
    logger.info("=" * 60)
    
    # Fetch videos
    videos = fetch_mrballen_videos()
    
    if not videos:
        logger.warning(f"No videos found for {CHANNEL_NAME} channel")
        return
    
    logger.info(f"Found {len(videos)} videos to process")
    
    # Initialize Selenium driver
    try:
        driver = get_selenium_driver()
    except Exception as e:
        logger.error(f"Failed to initialize Selenium driver: {e}")
        return
    
    try:
        # Process each video
        for i, video in enumerate(videos, 1):
            logger.info(f"\nProcessing video {i}/{len(videos)}")
            
            try:
                process_video(video, driver)
                
                # Add delay between videos
                if i < len(videos):
                    delay = 5  # seconds
                    logger.info(f"Waiting {delay} seconds before next video...")
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"Error processing video {video['video_id']}: {e}")
                continue
    
    finally:
        logger.info("Closing browser...")
        driver.quit()
        logger.info("Scraper completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nScraper interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
