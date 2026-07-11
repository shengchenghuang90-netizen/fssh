import os
import requests
from bs4 import BeautifulSoup
import logging

# 設定日誌格式，方便在 GitHub Actions 查看
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從 GitHub Secrets 讀取 Discord Webhook 網址
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FILE_NAME = "last_title.txt"

def get_latest_fssh_news():
    # 鳳山高中最新消息列表的專屬網址
    url = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php?uid=WID_0_2_0f075596d6cfd282f38872677912f105e9857086&maximize=1&allbtn=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 尋找網頁中所有的超連結 <a>
        for a in soup.find_all("a"):
            title = a.text.strip()
            link = a.get("href", "")
            
            # 排除常見的選單按鈕，字數大於 10 通常就是真正的公告標題
            ignore_words = ["首頁", "上一頁", "下一頁", "最後一頁", "登入", "國立鳳山高級中學", "RSS"]
            if len(title) > 10 and not any(w in title for w in ignore_words):
                
                # 處理 ischool 系統常見的 javascript 隱藏網址
                if "javascript" in link or link == "#":
                    # 直接把連結設定為這個公告列表的網址，方便手機點擊查看
                    link = url
                elif link.startswith("/"):
                    link = "https://www.fssh.khc.edu.tw" + link
                elif link.startswith("?"):
                    link = "https://www.fssh.khc.edu.tw/ischool/widget/site_news/main2.php" + link
                    
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
            
    # 判斷是不是新的公告
    if title != last_title:
        logging.info(f"🎉 發現新公告：{title}，準備發送 Discord！")
        
        if DISCORD_WEBHOOK_URL:
            payload = {
                "content": f"🔔 **鳳山高中最新公告出爐囉！**\n📌 **標題**：{title}\n🔗 **連結**：{link}"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            logging.info("✅ Discord 通知發送成功！")
        else:
            logging.error("❌ 發送失敗：讀取不到 Discord Webhook，請檢查 GitHub Secrets 設定！")
            
        # 將新的標題存起來，下次就不會重複發送
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(title)
    else:
        logging.info(f"目前沒有新公告 (最新的一筆仍是: {title[:10]}...)，安全無事。")

if __name__ == "__main__":
    main()
