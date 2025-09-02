import feedparser
import requests
import json
import time
import os

# --- ⚙️ الإعدادات: تم تحديث قائمة الـ RSS ⚙️ ---

import os # تأكد من إضافة هذا السطر في أعلى الملف مع باقي الـ imports
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# الـ Chat ID الخاص بقناتك
TELEGRAM_CHAT_ID = "-1002320540733"

# قائمة روابط الـ RSS الجديدة التي طلبتها
RSS_FEEDS = [
    "https://feeds.alwatanvoice.com/ar/palestine.xml",
    "http://feeds.bbci.co.uk/arabic/middleeast/rss.xml",
    "https://www.france24.com/ar/middle-east/rss",
    "https://www.pbc.ps/feed/",
    "https://palinfo.com/feed/",
    "https://pnn.ps/feed",
    "https://arabic.rt.com/rss/",
    "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9"
]

# الكلمات المفتاحية للفلتر (ما زالت موجودة وفعالة)
KEYWORDS = [
    "فلسطين", "غزة", "الضفة", "القدس", "رام الله", 
    "حماس", "فتح", "استشهاد", "شهيد", "قصف", "غارة", "اقتحام", "صواريخ", "اشتباكات"
]

# اسم الملف الذي سنحفظ فيه روابط الأخبار التي تم إرسالها (لمنع التكرار)
SENT_LINKS_FILE = "sent_links.json"

# --- 🤖 منطق عمل البوت (لا تحتاج لتعديل هذا الجزء) 🤖 ---

def load_sent_links():
    """تحميل الروابط المرسلة سابقاً من الملف"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, SENT_LINKS_FILE)
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r') as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()

def save_sent_links(links):
    """حفظ الروابط المحدثة في الملف"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, SENT_LINKS_FILE)
    with open(file_path, 'w') as f:
        json.dump(list(links), f)

def send_to_telegram(title, link, source):
    """إرسال الرسالة المنسقة إلى تيليجرام"""
    message = (
        f"🇵🇸 <b>{source}</b>\n\n"
        f"<b><a href='{link}'>{title}</a></b>"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status() # Check for HTTP errors
        print(f"✅ تم إرسال الخبر بنجاح: {title}")
    except requests.exceptions.RequestException as e:
        print(f"❌ فشل إرسال الخبر: {e}")

def main():
    """الوظيفة الرئيسية للسكربت"""
    print("🚀 بدء جولة التحقق من الأخبار الجديدة...")
    sent_links = load_sent_links()
    new_links_found = False

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get('title', 'مصدر غير معروف')
            print(f"🔍 يتم التحقق من: {source_name}")

            # Check if there are entries in the feed
            if not feed.entries:
                print(f"🟡 لا توجد عناصر في الرابط: {source_name}")
                continue

            for entry in reversed(feed.entries): # reversed to process oldest first
                link = entry.get('link')
                title = entry.get('title')

                if not link or not title:
                    continue # Skip entry if essential data is missing

                if link in sent_links:
                    continue # تخطي الخبر إذا تم إرساله من قبل

                content_to_check = title + entry.get('summary', '')
                if not KEYWORDS or any(keyword.lower() in content_to_check.lower() for keyword in KEYWORDS):
                    send_to_telegram(title, link, source_name)
                    sent_links.add(link)
                    new_links_found = True
                    time.sleep(1) # تأخير بسيط بين الرسائل لتجنب الحظر
            
        except Exception as e:
            print(f"⚠️ حدث خطأ أثناء معالجة الرابط {feed_url}: {e}")

    if new_links_found:
        save_sent_links(sent_links)
        print("💾 تم حفظ الروابط الجديدة.")
    else:
        print("🛌 لا توجد أخبار جديدة تستوفي الشروط.")
    
    print("🏁 انتهت جولة التحقق.")


if __name__ == "__main__":
    main()
