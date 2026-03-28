import asyncio
import re
import requests
from telethon import TelegramClient, events
from openai import OpenAI

# ===== CONFIG =====
api_id = 36935944
api_hash = "76e7dbf85f9b4121cf2368f8c981537f"

destination_channel = -1003830464685
affiliate_tag = "lootradar21-21"
OPENAI_API_KEY = "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"  # ⚠️ use new key

source_channels = [
    -1001246257619,
    -1001407365889,
    -1002393042058,
    -1001179165333,
    -1002200312455
]

# ===== INIT =====
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===== LINK FUNCTIONS =====

def expand_url(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
        return response.url
    except:
        return url

def extract_asin(url):
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    return None

def build_affiliate_link(url):
    expanded = expand_url(url)
    asin = extract_asin(expanded)

    if asin:
        return f"https://www.amazon.in/dp/{asin}?tag={affiliate_tag}"
    
    return expanded

def remove_links(text):
    return re.sub(r'http\S+', '', text)

# ===== AI CAPTION =====

def generate_caption(text, link):
    clean_text = remove_links(text)
    title = clean_text.split("\n")[0].strip()

    prompt = f"""
Create a high-converting Telegram deal post.

Rules:
- Max 5 lines
- Use emojis
- Add urgency (limited deal)
- Strong CTA
- Keep it short

Product:
{title}

Link:
{link}
"""

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except:
        # fallback if API fails
        return f"""🔥 HOT DEAL ALERT!

{title}

👉 Buy Now: {link}

⚡ Limited time deal!
"""

# ===== MAIN =====

async def main():
    client = TelegramClient('render_session', api_id, api_hash)
    await client.start()

    print("🚀 BOT LIVE...")

    @client.on(events.NewMessage)
    async def handler(event):

        print("Incoming:", event.chat_id, flush=True)

        if event.chat_id not in source_channels:
            return

        text = event.message.message

        if not text:
            return

        if "amazon" not in text.lower() and "amzn.to" not in text:
            return

        links = re.findall(r'(https?://\S+)', text)

        link = None
        for l in links:
            if "amazon" in l or "amzn.to" in l:
                link = l
                break

        if not link:
            return

        clean_link = build_affiliate_link(link)

        # 🚀 AI caption here
        caption = generate_caption(text, clean_link)

        await client.send_message(destination_channel, caption, link_preview=True)

        print("✅ AI DEAL POSTED", flush=True)

    await client.run_until_disconnected()

# ===== RUN =====
asyncio.run(main())
