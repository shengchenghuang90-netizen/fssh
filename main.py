import os
import logging
from playwright.sync_api import sync_playwright
import requests

# 設定日誌格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HISTORY_FILE = "history_links.txt"

def get_latest_fssh_news():
    url = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php?uid=WID_0_2_0f075596d6cfd282f38872677912f105e9857086&maximize=1&allbtn=0"
    
    with sync_playwright() as p:
        # headless=True 是節省效能的關鍵
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            links = page.query_selector_all("a")
            news_list = []
            
            for link in links:
                title = link.inner_text().strip()
                href = link.get_attribute("href")
                
                ignore_words = ["首頁", "上一頁", "下一頁", "第一頁", "最後一頁", "登入", "網站導覽", "more", "詳細內容"]
                
                if len(title) > 6 and not any(w in title for w in ignore_words):
                    # 連結美化：無效連結統一導向官網
                    if not href or "javascript" in href:
                        final_link = "https://www.fssh.khc.edu.tw"
                    elif href.startswith("?"):
                        final_link = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php" + href
                    elif href.startswith("/"):
                        final_link = "https://www.fssh.khc.edu.tw" + href
                    else:
                        final_link = href
                    
                    news_list.append({"title": title, "link": final_link})
            
            browser.close()
            return news_list[:5] # 抓取最新的 5 則
            
        except Exception as e:
            logging.error(f"抓取過程發生錯誤: {e}")
            browser.close()
            return []

def main():
    news_items = get_latest_fssh_news()
    if not news_items:
        logging.warning("未能獲取公告，可能網頁結構變更或網路異常。")
        return

    # 讀取已發送過的歷史連結
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = f.read().splitlines()

    # 找出未發送過的項目
    new_items = [item for item in news_items if item["link"] not in history]

    if new_items:
        # 從舊到新順序發送
        for item in reversed(new_items):
            if DISCORD_WEBHOOK_URL:
                payload = {"content": f"🔔 **鳳山高中最新公告**\n📌 **{item['title']}**\n🔗 {item['link']}"}
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
            history.append(item["link"])
        
        # 安全寫入：確保檔案不會被意外清空
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(history[-20:]))
        logging.info(f"成功發送 {len(new_items)} 則新公告。")
    else:
        logging.info("無新公告。")

if __name__ == "__main__":
    main()
