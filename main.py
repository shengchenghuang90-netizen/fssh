import os
import logging
from playwright.sync_api import sync_playwright
import requests

# 設定日誌格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從環境變數讀取 Webhook
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    # 鳳山高中專屬公告頁面
    url = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php?uid=WID_0_2_0f075596d6cfd282f38872677912f105e9857086&maximize=1&allbtn=0"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            links = page.query_selector_all("a")
            for link in links:
                title = link.inner_text().strip()
                href = link.get_attribute("href")
                
                ignore_words = ["首頁", "上一頁", "下一頁", "第一頁", "最後一頁", "登入", "網站導覽", "more", "詳細內容"]
                
                if len(title) > 6 and not any(w in title for w in ignore_words):
                    logging.info(f"成功找到目標：{title}")
                    
                    # 🎯 統一指向學校官網的邏輯
                    if not href or "javascript" in href:
                        final_link = "https://www.fssh.khc.edu.tw"
                    elif href.startswith("?"):
                        final_link = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php" + href
                    elif href.startswith("/"):
                        final_link = "https://www.fssh.khc.edu.tw" + href
                    else:
                        final_link = href
                        
                    browser.close()
                    return title, final_link
        except Exception as e:
            logging.error(f"抓取過程發生錯誤: {e}")
        
        browser.close()
        return None, None

def main():
    logging.info("正在執行瀏覽器爬蟲...")
    title, link = get_latest_fssh_news()
    
    if not title:
        logging.warning("未能獲取公告，請檢查網站是否結構變更。")
        return

    # 檢查是否為新公告 (比對記憶檔)
    last_title = ""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    if title != last_title:
        logging.info(f"發現新公告：{title}")
        if DISCORD_WEBHOOK_URL:
            # 傳送 Discord 訊息
            payload = {"content": f"🔔 **鳳山高中最新公告**\n📌 **{title}**\n🔗 {link}"}
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            
            # 更新記憶檔
            with open(FILE_NAME, "w", encoding="utf-8") as f:
                f.write(title)
            logging.info("通知已發送至 Discord。")
    else:
        logging.info("無新公告，不發送通知。")

if __name__ == "__main__":
    main()
