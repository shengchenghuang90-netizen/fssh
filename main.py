import os
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    # 這裡已經換成你剛剛找到的「真正公告列表」網址
    url = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php?uid=WID_0_2_0f075596d6cfd282f38872677912f105e9857086&maximize=1&allbtn=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 尋找表格內的超連結
        for tr in soup.find_all("tr"):
            a = tr.find("a")
            if a and a.get("href"):
                title = a.text.strip()
                link = a["href"]
                
                # 排除太短的無效標題或 javascript 按鈕
                if len(title) > 5 and "javascript" not in link:
                    # 處理網址格式，確保點擊後能直接連回學校網站
                    if link.startswith("/"):
                        link = "https://www.fssh.khc.edu.tw" + link
                    elif link.startswith("?"):
                        link = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php" + link
                        
                    return title, link
    except Exception as e:
        logging.error(f"網頁抓取失敗: {e}")
    return None, None

def main():
    logging.info("正在檢查最新公告...")
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
                "content": f"🔔 **最新公告出爐囉！**\n📌 **標題**：{title}\n🔗 **連結**：{link}"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
        else:
            logging.error("發送失敗：讀取不到 Discord Webhook！")
            
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(title)
    else:
        logging.info("目前沒有新公告，安全無事。")

if __name__ == "__main__":
    main()
