import asyncio
import re
import requests
import random
import os
import threading
from datetime import datetime
from telethon import TelegramClient, events
from flask import Flask
from openai import OpenAI
WEBHOOK_URL = "https://hook.eu1.make.com/x7rje41fui0106impkl7fkygggorl5fk"

def send_to_make(title, link):
    data = {
        "title": title,
        "link": link
    }

    try:
        requests.post(WEBHOOK_URL, json=data)
        print("📤 Sent to Make", flush=True)
    except Exception as e:
        print("Webhook error:", e, flush=True)

# ===== CONFIG =====
api_id = 36935944
api_hash = "76e7dbf85f9b4121cf2368f8c981537f"

destination_channel = -1003830464685
affiliate_tag = "lootradar21-21"

source_channels = [
    -1001246257619,
    -1001407365889,
    -1002393042058,
    -1001179165333,
    -1002200312455
]

OPENAI_API_KEY = os.getenv("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")
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===== FLASK (KEEP RENDER ALIVE) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "LootRadar Bot Running ✅"

# ===== LINK FUNCTIONS =====

def expand_url(url):
    try:
        return requests.get(url, allow_redirects=True, timeout=5).url
    except:
        return url

def extract_asin(url):
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    return match.group(1) if match else None

def build_affiliate_link(url):
    expanded = expand_url(url)
    asin = extract_asin(expanded)

    if asin:
        return f"https://www.amazon.in/dp/{asin}?tag={affiliate_tag}"
    return expanded

# ===== AI CAPTION =====

def generate_caption(title, link, prefix):

    cta_list = [
        "📢 Join for daily Amazon deals 👉 https://t.me/smartlootradar",
        "🔥 Don’t miss deals! Join now 👉 https://t.me/smartlootradar",
        "⚡ Live deals here 👉 https://t.me/smartlootradar",
    ]

    forward_line = "🔁 Share with friends who love deals!"
    cta = random.choice(cta_list)

    prompt = f"""
Create a high-converting Telegram deal post.

Rules:
- Max 4 lines
- Use emojis
- Add urgency
- Strong CTA

Product:
{title}
"""

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        ai_text = response.choices[0].message.content.strip()
    except:
        ai_text = title

    return f"""{prefix}

{ai_text}

👉 Buy Now: {link}

⚡ Limited time deal!

{forward_line}

{cta}
"""

# ===== MAIN BOT =====

async def main():
    import os

    print("🔥 Entered main()", flush=True)
    print("📂 Checking session file...", flush=True)
    print("Files in dir:", os.listdir(), flush=True)

    client = TelegramClient('render_session', api_id, api_hash)
    await client.start()

    print("🚀 BOT LIVE...", flush=True)

    posted_links = set()

    @client.on(events.NewMessage)
    async def handler(event):

        if event.chat_id not in source_channels:
            return

        text = event.message.message or event.raw_text or ""

        print("\n📩 Incoming:", event.chat_id, flush=True)
        print("Message:", text[:100], flush=True)

        # ===== EXTRACT LINKS (ADVANCED) =====
        links = []

        links += re.findall(r'(https?://\S+)', text)

        if event.message.entities:
            for ent in event.message.entities:
                try:
                    if hasattr(ent, 'url') and ent.url:
                        links.append(ent.url)
                except:
                    pass

        print("Extracted links:", links, flush=True)

        if not links:
            print("❌ No link found", flush=True)
            return

        link = None
        for l in links:
            if "amazon" in l or "amzn" in l:
                link = l
                break

        if not link:
            link = links[0]

        clean_link = build_affiliate_link(link)

        if clean_link in posted_links:
            print("⚠️ Duplicate skipped", flush=True)
            return

        posted_links.add(clean_link)

        # ===== CLEAN TEXT =====
        clean_text = re.sub(r'http\S+', '', text)

        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]

        title = "Hot Deal"
        for line in lines:
            if len(line) > 10 and not line.isdigit():
                title = line
                break

        # ===== DEAL SCORING =====
        score = 0
        t = text.lower()

        if "₹" in t: score += 1
        if any(w in t for w in ["deal", "offer", "loot"]): score += 2
        if any(w in t for w in ["limited", "ending"]): score += 2

        if score >= 4:
            prefix = "🔥 MEGA DEAL!"
        elif score >= 2:
            prefix = "⚡ HOT DEAL!"
        else:
            prefix = "💡 DEAL"

        # ===== GENERATE CAPTION =====
caption = generate_caption(title, clean_link, prefix)

msg = await client.send_message(destination_channel, caption, link_preview=True)

send_to_make(caption, clean_link)

# ===== AUTO PIN =====
if "🔥" in prefix:
    try:
        await client.pin_message(destination_channel, msg.id)
    except:
        pass

        print("✅ DEAL POSTED", flush=True)

    await client.run_until_disconnected()

# ===== RUN BOT + FLASK =====

def run_bot():
    import time
    while True:
        try:
            print("🚀 Starting bot...", flush=True)
            asyncio.run(main())
        except Exception as e:
            print("❌ BOT ERROR:", e, flush=True)
            time.sleep(5)

if __name__ == "__main__":
    import threading

    t = threading.Thread(target=run_bot)
    t.start()

    print("🌐 Starting Flask...", flush=True)
    app.run(host="0.0.0.0", port=10000)