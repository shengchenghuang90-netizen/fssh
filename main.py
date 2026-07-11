import os
import logging
from playwright.sync_api import sync_playwright
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    url = "https://www.fssh.khc.edu.tw/home"
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        
        # 等待網頁裡的公告表格出現 (這裡給它 10 秒鐘讓 JavaScript 跑完)
        page.wait_for_selector("table", timeout=10000)
        
        # 抓取第一筆公告的標題與連結
        # 這裡使用 CSS Selector 語法直接定位
        first_news = page.query_selector("table a")
        
        title = first_news.inner_text().strip() if first_news else None
        link = first_news.get_attribute("href") if first_news else None
        
        browser.close()
        return title, link

def main():
    logging.info("正在啟動虛擬瀏覽器抓取公告...")
    title, link = get_latest_fssh_news()
    
    if not title:
        logging.error("抓取失敗，可能網頁結構改變。")
        return

    # 後續發送 Discord 的邏輯維持不變
    last_title = ""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    if title != last_title:
        logging.info(f"🎉 發現新公告：{title}")
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🔔 **鳳山高中最新公告**\n📌 {title}\n🔗 {link}"})
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(title)

if __name__ == "__main__":
    main()
