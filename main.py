import os
import requests
from bs4 import BeautifulSoup
import logging

# 設定日誌格式，讓 GitHub Actions 可以印出漂亮的執行紀錄
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從 GitHub Secrets 自動讀取 Discord 網址
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    url = "https://www.fssh.khc.edu.tw/home"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 精準解析鳳中網站表格結構，抓取第一條實質公告
        for tr in soup.find_all("tr"):
            a = tr.find("a")
            if a and a.get("href"):
                title = a.text.strip()
                link = a["href"]
                if len(title) > 5 and "home" not in link:
                    if link.startswith("/"):
                        link = "https://www.fssh.khc.edu.tw" + link
                    return title, link
    except Exception as e:
        logging.error(f"網頁抓取失敗: {e}")
    return None, None

def main():
    logging.info("正在檢查鳳山高中最新公告...")
    title, link = get_latest_fssh_news()
    
    if not title:
        logging.warning("無法獲取公告，稍後重試。")
        return

    last_title = ""
    # 讀取本地端的紀錄檔
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    # 判斷是否為新公告
    if title != last_title:
        logging.info(f"🎉 發現新公告：{title}，準備發送 Discord！")
        
        if DISCORD_WEBHOOK_URL:
            payload = {
                "content": f"🔔 **鳳山高中官網有新公告囉！**\n📌 **標題**：{title}\n🔗 **連結**：{link}"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
        else:
            logging.error("發送失敗：讀取不到 Discord Webhook，請檢查 Secrets 設定！")
            
        # 將新標題寫入記憶檔案
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(title)
    else:
        logging.info("目前沒有新公告，安全無事。")

if __name__ == "__main__":
    main()
