import os
import time
import feedparser
import requests
from openai import OpenAI

# --- CẤU HÌNH THÔNG TIN CỦA BẠN ---
# 1. Thay bằng OpenAI API Key của bạn
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# 2. Thay bằng Telegram Bot Token từ BotFather
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# 3. Thay bằng Username nhóm Telegram hoặc ID nhóm của bạn (vd: @ten_nhom)
TELEGRAM_CHAT_ID = "@YOUR_TELEGRAM_GROUP_USERNAME"

# 4. Thay bằng tài khoản X (Twitter) muốn theo dõi (không cần dấu @)
X_USERNAME = "alpix_io"

# File lưu ID bài đã xử lý để tránh đăng trùng
SEEN_POSTS_FILE = "seen_posts.txt"


def load_seen_posts():
  if not os.path.exists(SEEN_POSTS_FILE):
    return set()
  with open(SEEN_POSTS_FILE, "r") as f:
    return set(line.strip() for line in f)


def save_seen_post(post_id):
  with open(SEEN_POSTS_FILE, "a") as f:
    f.write(f"{post_id}\n")


def get_latest_tweets_via_rss(username):
  # Sử dụng dịch vụ RSS trung gian để lấy bài miễn phí
  rss_url = f"https://nitter.net/{username}/rss"
  feed = feedparser.parse(rss_url)
  posts = []
  for entry in feed.entries[:5]:
    posts.append({
        "id": entry.id,
        "title": entry.title,
        "link": entry.link,
    })
  return posts


def ai_rewrite_content(original_text):
  """Dùng AI để tóm tắt hoặc viết lại nội dung bài đăng theo ý muốn"""
  prompt = (
      "Hãy đọc nội dung bài viết trên X sau đây, tóm tắt lại hoặc viết lại"
      " bằng tiếng Việt thật sinh động, ngắn gọn kèm emoji phù hợp để đăng"
      " nhóm Telegram:\n\n"
      f"{original_text}"
  )

  try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "Bạn là trợ lý biên tập nội dung chuyên nghiệp.",
        }, {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
  except Exception as e:
    print(f"Lỗi gọi OpenAI API: {e}")
    return original_text


def send_to_telegram(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": text,
      "disable_web_page_preview": False,
  }
  requests.post(url, json=payload)


def main():
  print(f"AI Bot đang khởi động, theo dõi tài khoản @{X_USERNAME}...")
  seen_posts = load_seen_posts()

  while True:
    try:
      posts = get_latest_tweets_via_rss(X_USERNAME)
      for post in reversed(posts):
        post_id = post["id"]
        if post_id in seen_posts:
          continue

        original_text = post["title"]
        post_link = post["link"]

        # Gọi AI xử lý nội dung
        print(f"Đang xử lý bài viết mới: {post_id}")
        ai_text = ai_rewrite_content(original_text)

        # Ghép nội dung hoàn chỉnh
        final_message = f"{ai_text}\n\n🔗 Nguồn: {post_link}"

        # Gửi lên nhóm Telegram
        send_to_telegram(final_message)

        # Lưu lại trạng thái đã đăng
        save_seen_post(post_id)
        seen_posts.add(post_id)

    except Exception as e:
      print(f"Lỗi vòng lặp chính: {e}")

    # Kiểm tra lại sau mỗi 3 phút
    time.sleep(180)


if __name__ == "__main__":
  main()
