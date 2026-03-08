#!/usr/bin/env python3
"""
Watches for @solidifiedplaydoh mentions, sends to OpenRouter, types reply with pyautogui + Enter.

Two modes:
  --bot   (default) Uses a Discord bot - works everywhere, no proxy. Bot must be in your servers.
  --proxy Uses mitmproxy to intercept your Discord traffic - requires proxy setup, browser only.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from urllib.error import HTTPError

from dotenv import load_dotenv

# Load .env from script directory
_script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_script_dir, ".env"), override=True)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "arcee-ai/trinity-large-preview:free"
TARGET_USERNAME = "solidifiedplaydoh"

# Set by READY event
_our_user_id: str | None = None
# Set DISCORD_MONITOR_DEBUG=1 to log all Discord WebSocket traffic
_DEBUG = os.getenv("DISCORD_MONITOR_DEBUG", "").strip().lower() in ("1", "true", "yes")

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import pyautogui
except ImportError:
    pyautogui = None


def _paste_and_send(text: str) -> bool:
    """Copy to clipboard, then Cmd+V + Enter. Uses AppleScript (reliable on macOS)."""
    if not text:
        return False
    if not _copy_to_clipboard(text):
        return False
    try:
        delay = float(os.getenv("DISCORD_MONITOR_TYPE_DELAY", "0"))
        if delay > 0:
            import time
            time.sleep(delay)
        # AppleScript: Cmd+V then Enter (more reliable than pyautogui on macOS)
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down', "-e", 'tell application "System Events" to key code 36'],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"[paste] Failed: {e}", file=sys.stderr)
        return False


def _copy_to_clipboard(text: str) -> bool:
    if not text:
        return False
    try:
        if pyperclip:
            pyperclip.copy(text)
        else:
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        return True
    except Exception as e:
        print(f"[clipboard] Failed: {e}", file=sys.stderr)
        return False


def _show_notification(title: str, body: str, subtitle: str = "") -> None:
    """Show a macOS notification."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    try:
        script = f'display notification "{esc(body)}" with title "{esc(title)}"'
        if subtitle:
            script += f' subtitle "{esc(subtitle)}"'
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    except Exception:
        pass


def _call_openrouter(api_key: str, query: str, author: str, channel_id: str, parent_content: str | None = None) -> str:
    """Sync call to OpenRouter. Returns model reply. parent_content = message being replied to (for context)."""
    system = (
        "You are helping Solidified respond to Discord messages. "
        "Someone mentioned @solidifiedplaydoh. Reply as if you are Solidified - concise, natural, helpful. "
        "Keep responses short (1-3 sentences) unless the question needs more."
    )
    user_msg = f"{author} asked: {query}"
    if parent_content:
        user_msg = f"{author} is replying to: \"{parent_content}\"\n{author} says: {query}"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Solidifiedplaydoh",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return f"[OpenRouter error {e.code}]: {body}"
    except Exception as e:
        return f"[OpenRouter error]: {e}"
    choices = data.get("choices", [])
    if not choices:
        return "[No response from model]"
    content = choices[0].get("message", {}).get("content", "").strip()
    return content or "[Empty response]"


def _extract_query_after_mention(content: str, our_id: str) -> str:
    """Remove our <@ID> mention and return the rest, trimmed."""
    # Remove <@USER_ID> or <@!USER_ID>
    cleaned = re.sub(rf"<@!?{re.escape(our_id)}>\s*", "", content, flags=re.IGNORECASE)
    return cleaned.strip()


def _mentions_us(data: dict) -> bool:
    global _our_user_id
    if not _our_user_id:
        return False
    mentions = data.get("mentions") or []
    for m in mentions:
        if isinstance(m, dict) and m.get("id") == _our_user_id:
            return True
        if isinstance(m, str) and m == _our_user_id:
            return True
    # Fallback: username in mentions
    for m in mentions:
        if isinstance(m, dict):
            uname = (m.get("username") or m.get("global_name") or "").lower()
            if uname == TARGET_USERNAME.lower():
                return True
    return False


def websocket_message(flow):
    """mitmproxy addon hook: process each WebSocket message."""
    if flow.websocket is None:
        return

    last = flow.websocket.messages[-1]
    # Only process messages FROM Discord (server -> client)
    if last.from_client:
        return

    raw = last.content if isinstance(last.content, bytes) else last.content.encode()
    try:
        msg = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    op = msg.get("op")
    t = msg.get("t")
    d = msg.get("d") or {}

    global _our_user_id

    if _DEBUG and t:
        print(f"[discord_mention_monitor] WS event: {t}", file=sys.stderr)

    # READY: capture our user ID
    if t == "READY":
        user = d.get("user") or {}
        uid = user.get("id")
        if uid:
            _our_user_id = str(uid)
            print(f"[discord_mention_monitor] Logged in as user {_our_user_id}", file=sys.stderr)

    # MESSAGE_CREATE: check for @solidifiedplaydoh
    if t != "MESSAGE_CREATE":
        return

    if not _mentions_us(d):
        return

    content = (d.get("content") or "").strip()
    if not content:
        return

    author = "unknown"
    a = d.get("author") or {}
    if isinstance(a, dict):
        author = a.get("username") or a.get("global_name") or author
    channel_id = d.get("channel_id", "?")

    query = _extract_query_after_mention(content, _our_user_id) if _our_user_id else content
    if not query:
        query = content  # fallback: use full content

    # Reply context: Discord includes referenced_message when it's a reply
    parent_content = None
    ref_msg = d.get("referenced_message")
    if isinstance(ref_msg, dict):
        parent_content = (ref_msg.get("content") or "").strip()[:500]
        if parent_content:
            print(f"[discord_mention_monitor] Reply context: {parent_content[:60]}...", file=sys.stderr)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[discord_mention_monitor] OPENROUTER_API_KEY not set", file=sys.stderr)
        return

    print(f"[discord_mention_monitor] Mention from {author}: {query[:80]}...", file=sys.stderr)
    reply = _call_openrouter(api_key, query, author, channel_id, parent_content)

    text_to_send = f"```\n{reply}\n```"
    _show_notification("Discord Mention", "Pasting now — focus Discord!", f"From {author}")
    if _paste_and_send(text_to_send):
        print(f"[discord_mention_monitor] Pasted and sent ({len(text_to_send)} chars)", file=sys.stderr)
    else:
        print(f"[discord_mention_monitor] Response:\n{reply}", file=sys.stderr)


def _run_bot_mode():
    """Bot mode: uses a Discord bot to listen for mentions. Works with desktop + browser."""
    import discord
    from discord.ext import commands

    token = os.getenv("MONITOR_BOT_TOKEN") or os.getenv("other_bot_token")
    if not token:
        print("ERROR: Set MONITOR_BOT_TOKEN or other_bot_token in .env", file=sys.stderr)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"[discord_mention_monitor] Bot ready — watching for @{TARGET_USERNAME}", file=sys.stderr)
        print("[discord_mention_monitor] On mention: pastes reply instantly. Keep Discord message box focused!", file=sys.stderr)
        print("[discord_mention_monitor] macOS: Grant Accessibility in System Settings > Privacy if typing fails.", file=sys.stderr)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        # Check if message mentions solidifiedplaydoh
        name_lower = TARGET_USERNAME.lower()
        mentioned = any(
            (u.name or "").lower() == name_lower or (u.global_name or "").lower() == name_lower
            for u in message.mentions
        ) or name_lower in (message.content or "").lower()
        if not mentioned:
            return

        content = (message.content or "").strip()
        author = str(message.author)
        channel_name = getattr(message.channel, "name", "dm") or "dm"

        # Extract text after our mention
        for u in message.mentions:
            if (u.name or "").lower() == name_lower or (u.global_name or "").lower() == name_lower:
                content = re.sub(rf"<@!?{u.id}>\s*", "", content, flags=re.IGNORECASE).strip()
                break
        if not content:
            content = (message.content or "").strip()

        # If replying to a message, fetch it for context
        parent_content = None
        if message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                parent_content = (ref_msg.content or "").strip()[:500]
                if parent_content:
                    print(f"[discord_mention_monitor] Reply context: {parent_content[:60]}...", file=sys.stderr)
            except Exception:
                pass

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("[discord_mention_monitor] OPENROUTER_API_KEY not set", file=sys.stderr)
            return

        print(f"[discord_mention_monitor] Mention from {author}: {content[:80]}...", file=sys.stderr)

        reply = _call_openrouter(api_key, content, author, str(getattr(message.channel, "id", "?")), parent_content)
        text_to_send = f"```\n{reply}\n```"
        _show_notification("Discord Mention", "Pasting now — focus Discord!", f"From {author}")
        if _paste_and_send(text_to_send):
            print(f"[discord_mention_monitor] Pasted and sent ({len(text_to_send)} chars)", file=sys.stderr)
        else:
            print(f"[discord_mention_monitor] Response:\n{reply}", file=sys.stderr)

    bot.run(token)


def _run_proxy_mode():
    """Proxy mode: mitmproxy intercepts Discord WebSocket traffic."""
    script_path = os.path.abspath(__file__)
    venv_bin = os.path.join(os.path.dirname(sys.executable), "mitmdump")
    port = os.getenv("DISCORD_MONITOR_PORT", "8082")
    print(f"[discord_mention_monitor] Starting mitmproxy on 127.0.0.1:{port}", file=sys.stderr)
    print(f"[discord_mention_monitor] Set system proxy to 127.0.0.1:{port}", file=sys.stderr)
    print("[discord_mention_monitor] Use Discord in a browser (discord.com) — desktop app ignores proxy.", file=sys.stderr)
    cmd = [venv_bin, "-s", script_path, "--listen-host", "127.0.0.1", "--listen-port", port]
    if not os.path.isfile(venv_bin):
        cmd = [sys.executable, "-m", "mitmproxy.tools.main", "mitmdump", "-s", script_path, "--listen-host", "127.0.0.1", "--listen-port", port]
    os.execv(cmd[0], cmd)


if __name__ == "__main__":
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    use_proxy = "--proxy" in sys.argv
    if use_proxy:
        _run_proxy_mode()
    else:
        _run_bot_mode()
