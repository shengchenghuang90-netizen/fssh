import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
FSSH_URL = "https://www.fssh.khc.edu.tw/home"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1525418350761742446/SF12GWts1jKb5zBJoNr_4H7SnzMiJCFjtbYUm1CgdbUEZsRAxfhN3eyn-hsd2lXADkeQ"
BUCKET_NAME = "gemini-cli-storage-581039"
LAST_TITLE_FILE_NAME = "last_title.txt"

# Initialize GCS client
storage_client = storage.Client()

def get_last_title(bucket_name, file_name):
    """Reads the last stored title from GCS."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        if blob.exists():
            last_title = blob.download_as_text()
            logging.info(f"Successfully retrieved last title from GCS: '{last_title}'")
            return last_title.strip()
        else:
            logging.info(f"'{file_name}' not found in bucket '{bucket_name}'. Assuming no previous title.")
            return None
    except Exception as e:
        logging.error(f"Error reading last title from GCS: {e}")
        return None

def save_last_title(bucket_name, file_name, title):
    """Saves the current title to GCS."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(title)
        logging.info(f"Successfully saved new title to GCS: '{title}'")
        return True
    except Exception as e:
        logging.error(f"Error saving last title to GCS: {e}")
        return False

def send_discord_message(webhook_url, title, link):
    """Sends a message to Discord via webhook."""
    message_content = {
        "content": f"鳳山高中新公告！\n**{title}**\n連結: {link}"
    }
    try:
        response = requests.post(webhook_url, json=message_content)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Discord message sent successfully for title: '{title}'")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Discord message: {e}")
        return False

def scrape_fssh_news(url):
    """Scrapes the FSSH website for the latest news title and link."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Adjust these selectors based on actual FSSH website structure ---
        # This is a common pattern for news lists. You might need to inspect
        # the FSSH website's HTML to find the correct selectors.
        # Example: Look for a div with a specific class, then an <a> tag inside it.
        
        # Attempt 1: Look for common news list items
        # This is a generic attempt. You might need to refine this.
        # For example, if news items are in a specific <ul> or <div class="news-section">
        
        # Let's try to find the main content area first
        main_content = soup.find('div', class_='main-content') or soup.find('main')
        if not main_content:
            logging.warning("Could not find main content area. Trying body directly.")
            main_content = soup.body

        # Look for common news/announcement patterns
        # This is highly dependent on the website's structure.
        # I'll try to find the first prominent link that might be a news item.
        
        # Common patterns: <a> tags within <li>, <p>, or directly under a news container
        # Let's try to find links that are likely news items.
        # This is a placeholder and will likely need adjustment.
        
        # A more robust approach would be to find a specific news section.
        # For now, let's try to find the first link in a common news-like container.
        
        # Example: Find a div with class 'news-list' or 'announcements'
        news_container = main_content.find('div', class_='news-list') or \
                         main_content.find('ul', class_='announcements') or \
                         main_content.find('div', class_='announcements') or \
                         main_content.find('div', class_='news-section')

        if news_container:
            first_news_link = news_container.find('a')
        else:
            # Fallback: try to find any prominent link in the main content
            first_news_link = main_content.find('a', href=True, string=lambda text: text and len(text) > 10) # Link with some text

        if first_news_link and first_news_link.get_text(strip=True):
            title = first_news_link.get_text(strip=True)
            relative_link = first_news_link['href']
            
            # Construct full URL if relative
            if relative_link.startswith('/'):
                full_link = FSSH_URL.rstrip('/') + relative_link
            else:
                full_link = relative_link # Assume it's already a full URL or relative to current path

            logging.info(f"Scraped latest news: Title='{title}', Link='{full_link}'")
            return title, full_link
        else:
            logging.warning("Could not find a suitable news title and link on the page.")
            return None, None

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error during scraping: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        return None, None

def fssh_news_checker(request):
    """
    Google Cloud Function entry point.
    Triggers the FSSH news scraping and Discord notification process.
    """
    logging.info("FSSH News Checker function triggered.")

    current_title, current_link = scrape_fssh_news(FSSH_URL)

    if not current_title:
        logging.error("Failed to scrape current news title. Exiting.")
        return 'Failed to scrape news', 500

    last_title = get_last_title(BUCKET_NAME, LAST_TITLE_FILE_NAME)

    if current_title != last_title:
        logging.info(f"New announcement detected! Old: '{last_title}', New: '{current_title}'")
        if send_discord_message(DISCORD_WEBHOOK_URL, current_title, current_link):
            save_last_title(BUCKET_NAME, LAST_TITLE_FILE_NAME, current_title)
            return 'New announcement found and notified!', 200
        else:
            return 'New announcement found but failed to notify Discord.', 500
    else:
        logging.info("No new announcement found.")
        return 'No new announcement.', 200

# For local testing (optional)
if __name__ == '__main__':
    # This block will only run when the script is executed directly, not as a Cloud Function.
    # You can simulate a request object if needed, or just call the core logic.
    logging.info("Running fssh_news_checker locally for testing.")
    # Simulate a dummy request object for local testing
    class DummyRequest:
        def get_json(self):
            return None
        def args(self):
            return None
    
    response, status_code = fssh_news_checker(DummyRequest())
    logging.info(f"Local test finished with status: {status_code}, message: {response}")
    print(f"Local test result: {response} (Status: {status_code})")