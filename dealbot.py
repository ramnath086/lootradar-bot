import asyncio
import re
import requests
import random
import os
import threading
from telethon import TelegramClient, events
from flask import Flask
from openai import OpenAI

# ===== INSTAGRAM =====
from instagrapi import Client
from PIL import Image, ImageDraw

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

# ===== OPENAI =====
OPENAI_API_KEY = os.getenv("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")
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===== INSTAGRAM CONFIG =====
INSTA_USERNAME = "amazon_deals88"
INSTA_PASSWORD = "Lootradar@86"

insta = Client()

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "LootRadar Bot Running ✅"

# ===== INSTAGRAM FUNCTIONS =====
def # insta_login()
    try:
        insta.login(INSTA_USERNAME, INSTA_PASSWORD)
        print("📸 Instagram login success", flush=True)
    except Exception as e:
        print("Instagram login error:", e, flush=True)

def create_image(title):
    img = Image.new('RGB', (1080, 1080), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((50, 400), title[:80], fill=(255, 255, 255))
    path = "deal.png"
    img.save(path)
    return path

def # post_to_instagram(title):
    try:
        img_path = create_image(title)

        caption = f"""🔥 DEAL ALERT!

{title}

💰 Limited time offer
👉 Link in bio

Follow @{INSTA_USERNAME}
"""

        insta.photo_upload(img_path, caption)
        print("📸 Posted to Instagram", flush=True)

    except Exception as e:
        print("Instagram error:", e, flush=True)

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

    print("🔥 Entered main()", flush=True)

    client = TelegramClient('render_session', api_id, api_hash)
    await client.start()

    print("🚀 BOT LIVE...", flush=True)

    insta_login()

    posted_links = set()

    @client.on(events.NewMessage)
    async def handler(event):

        if event.chat_id not in source_channels:
            return

        text = event.message.message or event.raw_text or ""

        print("\n📩 Incoming:", event.chat_id, flush=True)

        # ===== EXTRACT LINKS =====
        links = []
        links += re.findall(r'(https?://\S+)', text)

        if event.message.entities:
            for ent in event.message.entities:
                try:
                    if hasattr(ent, 'url') and ent.url:
                        links.append(ent.url)
                except:
                    pass

        if not links:
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
            return

        posted_links.add(clean_link)

        # ===== TITLE =====
        clean_text = re.sub(r'http\S+', '', text)
        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]

        title = "Hot Deal"
        for line in lines:
            if len(line) > 10 and not line.isdigit():
                title = line
                break

        # ===== PREFIX =====
        prefix = "🔥 MEGA DEAL!" if "₹" in text else "⚡ HOT DEAL!"

        # ===== CAPTION =====
        caption = generate_caption(title, clean_link, prefix)

        msg = await client.send_message(destination_channel, caption, link_preview=True)

        # ===== INSTAGRAM POST =====
        post_to_instagram(title)

        # ===== PIN =====
        if "🔥" in prefix:
            try:
                await client.pin_message(destination_channel, msg.id)
            except:
                pass

        print("✅ DEAL POSTED", flush=True)

    await client.run_until_disconnected()

# ===== RUN =====
def run_bot():
    import time
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print("❌ BOT ERROR:", e, flush=True)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)