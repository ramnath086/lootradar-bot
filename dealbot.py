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

from telethon import TelegramClient, events
from flask import Flask
from openai import OpenAI

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

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running ✅"

# ===== UTIL =====

def extract_price(text):
    match = re.search(r'₹\s?(\d+)', text)
    return match.group(1) if match else None

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

def generate_voice(title):
    try:
        speech = ai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=f"{generate_hook()}. {title}. Limited time deal."
        )
        path = "voice.mp3"
        with open(path, "wb") as f:
            f.write(speech.read())
        return path
    except:
        return None

def get_music():
    try:
        files = os.listdir("music")
        return os.path.join("music", random.choice(files)) if files else None
    except:
        return None

# ===== VIDEO GENERATION =====

def create_reel(img_path, title, text):
    output = f"reel_{int(time.time())}.mp4"

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

    client = TelegramClient('render_session', api_id, api_hash)
    await client.start()

    print("🚀 BOT LIVE")

    posted = set()

    @client.on(events.NewMessage)
    async def handler(event):

        if event.chat_id not in source_channels:
            return

        text = event.raw_text or ""

        links = re.findall(r'(https?://\S+)', text)
        if not links:
            return

        link = links[0]

        if link in posted:
            return

        posted.add(link)

        clean_text = re.sub(r'http\S+', '', text)
        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
        title = lines[0] if lines else "Hot Deal"

        prefix = "🔥 MEGA DEAL!" if "₹" in text else "⚡ HOT DEAL!"

        caption = generate_caption(title, link, prefix)

        msg = await client.send_message(destination_channel, caption)

        # ===== REEL GENERATION =====
        if event.message.photo:
            img = await event.download_media(file="product.jpg")

            video = create_reel(img, title, text)

            with open("reels_queue.txt", "a") as f:
                f.write(f"{video}|{title}\n")

            print("🎬 Reel created:", video)

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

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)