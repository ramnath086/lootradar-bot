import asyncio
import re
import requests
import random
import os
import threading
import subprocess
import time
import imageio_ffmpeg as ffmpeg

FFMPEG_PATH = ffmpeg.get_ffmpeg_exe()

import sqlite3
from telethon import TelegramClient, events
from flask import Flask
from openai import OpenAI

# ===== DATABASE =====

def init_db():
    conn = sqlite3.connect("deals.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS posted (url TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_posted(link):
    conn = sqlite3.connect("deals.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM posted WHERE url=?", (link,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_posted(link):
    conn = sqlite3.connect("deals.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posted (url) VALUES (?)", (link,))
    conn.commit()
    conn.close()

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
    -1002200312455,
    -1001273763977
]

OPENAI_API_KEY = "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"
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running ✅"

# ===== UTIL =====

def extract_price(text):
    match = re.search(r'₹\s?(\d+)', text)
    return match.group(1) if match else None

from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
import logging

def generate_hook():
    hooks = [
        "This deal will sell out fast 😳",
        "Amazon mistake deal 🚨",
        "Too cheap to ignore 🔥",
        "Limited stock alert ⚠️",
        "Hidden deal exposed 👀",
        "Big price drop today 💸",
        "Run before it’s gone 🏃",
        "Steal deal alert 🚀"
    ]
    return random.choice(hooks)

def convert_to_affiliate(url):
    try:
        # Expand URL if it's shortened
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        
        # Parse the expanded URL
        parsed = urlparse(final_url)
        
        # Add Amazon Affiliate Tag if it's an amazon domain
        if "amazon.in" in parsed.netloc or "amazon.com" in parsed.netloc:
            query_params = dict(parse_qsl(parsed.query))
            query_params["tag"] = affiliate_tag
            
            new_query = urlencode(query_params)
            new_parsed = parsed._replace(query=new_query)
            return urlunparse(new_parsed)
            
        return None
    except Exception as e:
        print("Affiliate conversion error:", e)
        return None

def generate_voice(title):
    try:
        speech = ai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=f"{generate_hook()}. {title}. Limited time deal."
        )
        path = "voice.mp3"
        with open(path, "wb") as f:
            f.write(speech.content)
        return path
    except Exception as e:
        print("Voice Error:", e)
        return None

def get_music():
    try:
        files = os.listdir("music")
        return os.path.join("music", random.choice(files)) if files else None
    except:
        return None

# ===== VIDEO GENERATION =====

def create_reel(img_path, title, text):
    os.makedirs("Insta posts", exist_ok=True)
    output = f"Insta posts/reel_{int(time.time())}.mp4"

    price = extract_price(text)
    mrp = str(int(price) + int(int(price)*0.5)) if price else ""

    voice = generate_voice(title)
    music = get_music()

    hook = generate_hook()
    safe_title = re.sub(r"[^\w\s]", "", title)[:40]

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.002,1.2)':d=125,"
        f"drawtext=text='{hook}':x=50:y=100:fontsize=60:fontcolor=red,"
        f"drawtext=text='{safe_title}':x=50:y=1400:fontsize=50:fontcolor=white,"
    )

    if price:
        vf += f"drawtext=text='₹{price}':x=50:y=1550:fontsize=80:fontcolor=yellow,"
    if mrp:
        vf += f"drawtext=text='₹{mrp}':x=300:y=1550:fontsize=60:fontcolor=gray,"

    vf += (
        "drawtext=text='LIMITED TIME ⏳':x=50:y=1700:fontsize=50:fontcolor=orange,"
        "drawtext=text='Follow @amazon_deals88':x=50:y=1850:fontsize=40:fontcolor=cyan"
    )

    cmd = [FFMPEG_PATH, "-loop", "1", "-i", img_path]

    if voice:
        cmd += ["-i", voice]
    if music:
        cmd += ["-i", music]

    cmd += [
        "-t", "6",
        "-vf", vf,
        "-pix_fmt", "yuv420p",
        "-y",
        output
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output

# ===== CAPTION =====

def generate_caption(title, link, prefix):
    return f"""{prefix}

🔥 {title}

👉 Buy Now: {link}

⚡ Limited time deal!
📢 Join 👉 https://t.me/smartlootradar
"""

# ===== MAIN =====

async def main():

    print("🔥 Entered main()", flush=True)

    import os

    print("Files:", os.listdir(), flush=True)

    print(
        "Session exists:",
        os.path.exists("render_session.session"),
        flush=True
    )

    client = TelegramClient(
        "render_session",
        api_id,
        api_hash
    )

    print("📡 Starting Telegram...", flush=True)

    await client.start()

    print("🚀 BOT LIVE", flush=True)

    @client.on(events.NewMessage)
    async def handler(event):

        print("EVENT CHAT ID:", event.chat_id, flush=True)

        if event.chat_id not in source_channels:
            return

        text = event.raw_text or ""

        links = re.findall(r'(https?://\S+)', text)
        if not links:
            return

        original_link = links[0]

        if is_posted(original_link):
            return

        mark_posted(original_link)

        link = convert_to_affiliate(original_link)
        
        if not link:
            return

        clean_text = re.sub(r'http\S+', '', text)
        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
        title = lines[0] if lines else "Hot Deal"

        prefix = "🔥 MEGA DEAL!" if "₹" in text else "⚡ HOT DEAL!"

        caption = generate_caption(title, link, prefix)

        caption = generate_caption(title, link, prefix)

        if event.message.photo:
            msg = await client.send_message(destination_channel, caption, file=event.message.photo)
            
            # ===== REEL GENERATION =====
            os.makedirs("Insta posts", exist_ok=True)
            img = await event.download_media(file=f"Insta posts/product_{int(time.time())}.jpg")

            video = create_reel(img, title, text)

            with open("reels_queue.txt", "a") as f:
                f.write(f"{video}|{title}\n")

            print("🎬 Reel created:", video)
        else:
            msg = await client.send_message(destination_channel, caption)

        print("✅ Posted")

    await client.run_until_disconnected()

# ===== RUN =====

def run_bot():
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

def run_bot():
    while True:
        try:
            print("🚀 Starting bot...", flush=True)
            asyncio.run(main())

        except Exception as e:
            import traceback

            print("❌ BOT ERROR:", e, flush=True)
            traceback.print_exc()

            time.sleep(5)


if __name__ == "__main__":

    print("🧵 Starting bot thread...", flush=True)

    t = threading.Thread(
        target=run_bot,
        daemon=True
    )

    t.start()

    print("🧵 Bot thread started", flush=True)

    print("🌐 Starting Flask...", flush=True)

    app.run(
        host="0.0.0.0",
        port=10000
    )