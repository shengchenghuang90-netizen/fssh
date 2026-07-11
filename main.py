import os
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    # 🎯 終極殺招：直接抓取 ischool 系統的 RSS 純資料來源
    url = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/rss.php?uid=WID_0_2_0f075596d6cfd282f38872677912f105e9857086"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        # 讓 BeautifulSoup 去解析 RSS (XML格式) 資料
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 在 RSS 裡，每一則公告都會被包在 <item> 標籤裡面
        item = soup.find("item")
        if item:
            # 直接精準抓出 <title> (標題) 和 <link> (連結)
            title = item.find("title").text.strip()
            link = item.find("link").text.strip()
            
            logging.info(f"成功透過 RSS 抓到最新公告：{title}")
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
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    if title != last_title:
        logging.info(f"🎉 發現新公告：{title}，準備發送 Discord！")
        
        if DISCORD_WEBHOOK_URL:
            payload = {
                "content": f"🔔 **鳳山高中最新公告出爐囉！**\n📌 **標題**：{title}\n🔗 **連結**：{link}"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            logging.info("✅ Discord 通知發送成功！")
        else:
            logging.error("❌ 發送失敗：讀取不到 Discord Webhook！")
            
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(title)
    else:
        logging.info(f"目前沒有新公告，安全無事。")

if __name__ == "__main__":
    main()
