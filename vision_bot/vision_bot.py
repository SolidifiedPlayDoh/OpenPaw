"""
Discord vision bot: @mention with text and/or images for AI analysis via Groq (Llama 4 Scout).
"""
import base64
import os
import sys

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env from parent project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(PARENT_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SYSTEM_PROMPT_FILE = os.path.join(PARENT_DIR, "config", "system_prompt.txt")

# Image MIME types supported by Discord
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def is_image_attachment(att: discord.Attachment) -> bool:
    """Check if attachment is an image (by filename or content_type)."""
    if att.filename:
        ext = os.path.splitext(att.filename.lower())[1]
        if ext in IMAGE_EXTENSIONS:
            return True
    if att.content_type and att.content_type.startswith("image/"):
        return True
    return False


async def fetch_image_as_base64(session: aiohttp.ClientSession, url: str) -> str | None:
    """Download image from URL and return as base64 data URL."""
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            content_type = resp.headers.get("Content-Type", "image/png")
            if "/" not in content_type:
                content_type = "image/png"
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception:
        return None


def load_system_prompt() -> str:
    """Load system prompt from config/system_prompt.txt (same as OpenPaw)."""
    if os.path.isfile(SYSTEM_PROMPT_FILE):
        try:
            with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except OSError:
            pass
    return ""


async def call_groq_vision(
    session: aiohttp.ClientSession,
    api_key: str,
    text: str,
    image_data_urls: list[str] | None = None,
    system_prompt: str = "",
) -> str | None:
    """Call Groq vision API with text and images."""
    content: list[dict] = []

    if text.strip():
        content.append({"type": "text", "text": text.strip()})

    for url in (image_data_urls or []):
        content.append({
            "type": "image_url",
            "image_url": {"url": url},
        })

    if not content:
        content = [{"type": "text", "text": "Hello, how can I help?"}]

    messages: list[dict] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.append({"role": "user", "content": content})

    payload = {
        "model": VISION_MODEL,
        "messages": messages,
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with session.post(GROQ_API_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                return f"API error {resp.status}: {err_text[:500]}"
            data = await resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            return msg.get("content") or "(no response)"
    except Exception as e:
        return f"Request failed: {e}"


def main() -> None:
    token = os.getenv("other_bot_token") or os.getenv("OTHER_BOT_TOKEN")
    api_key = os.getenv("GROQ_API_KEY")

    if not token:
        print("ERROR: other_bot_token or OTHER_BOT_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("ERROR: GROQ_API_KEY not set in .env (get one at console.groq.com)", file=sys.stderr)
        sys.exit(1)

    system_prompt = load_system_prompt()
    if system_prompt:
        print(f"Using system prompt from {SYSTEM_PROMPT_FILE}")

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.http_session: aiohttp.ClientSession | None = None

    @bot.event
    async def on_ready():
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=4)
        bot.http_session = aiohttp.ClientSession(connector=connector)
        print(f"Vision bot ready as {bot.user}")

    @bot.event
    async def on_disconnect():
        if bot.http_session:
            await bot.http_session.close()
            bot.http_session = None

    def get_session() -> aiohttp.ClientSession:
        if bot.http_session and not bot.http_session.closed:
            return bot.http_session
        return aiohttp.ClientSession()

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if not bot.user:
            return

        if bot.user not in message.mentions:
            return

        text = message.content or ""
        for u in message.mentions:
            text = text.replace(f"<@{u.id}>", "").strip()

        image_attachments = [a for a in message.attachments if is_image_attachment(a)]
        if not text.strip() and not image_attachments:
            await message.reply("Say something or send an image when you @ me.")
            return

        if not text.strip():
            text = "Describe this image in detail."

        await message.channel.typing()

        session = get_session()
        try:
            image_urls: list[str] = []
            for att in image_attachments:
                data_url = await fetch_image_as_base64(session, att.url)
                if data_url:
                    image_urls.append(data_url)
                if len(image_urls) >= 4:
                    break

            response = await call_groq_vision(session, api_key, text, image_urls if image_urls else None, system_prompt)
            if not response:
                await message.reply("No response from the AI.")
                return

            if len(response) > 1990:
                response = response[:1987] + "..."

            await message.reply(response)
        finally:
            if session is not bot.http_session:
                await session.close()

        await bot.process_commands(message)

    bot.run(token)


if __name__ == "__main__":
    main()
