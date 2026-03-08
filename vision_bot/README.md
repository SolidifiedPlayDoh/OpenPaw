# Vision Bot

Discord bot that uses Groq's Llama 4 Scout (free tier) for text and image analysis.

## Setup

1. Add your Groq API key to the parent project's `.env`:
   ```
   GROQ_API_KEY=gsk_...
   ```
   Get a key at [console.groq.com](https://console.groq.com) (free tier, no credit card).

2. Create venv and install deps:
   ```bash
   uv venv
   source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
   uv pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   uv run python vision_bot.py
   ```

## Usage

1. @mention the bot in any channel
2. Send text and/or attach images
3. The bot sends your message to Qwen3-VL and replies

- **Text only:** Ask anything (e.g. "Explain quantum computing")
- **Image + text:** "What's in this image?", "Describe this", etc.
- **Image only:** Defaults to "Describe this image in detail."

Uses Groq's free tier (1,000 requests/day).
