## OpenPaw Bot

Discord bot with reactions, AI chat (Groq/Llama 4 Scout, same as vision_bot), encryption tools, and voice. Reacts with your custom `:openpaw:` emoji.

### Quick start
1) Create a Discord application and bot at the Developer Portal.
2) On the Bot tab:
   - Enable Message Content Intent.
   - Copy the bot token.
3) Invite the bot to your server with scopes/permissions:
   - Scopes: `bot`, `applications.commands`
   - Read Messages/View Channels
   - Read Message History
   - Add Reactions
   - (Optional) Use External Emojis, if the emoji lives in a different server
4) Create a custom emoji in your server named `openpaw` (or set `EMOJI_ID`).
5) Setup env and deps:
   ```bash
   uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   uv pip install -r requirements.txt
   printf "DISCORD_TOKEN=your_token_here\nGUILD_ID=your_guild_id_optional\nEMOJI_NAME=openpaw\n" > .env
   ```
6) Run it:
   ```bash
   uv run bot.py
   ```

### Web dashboard
Run the bot and open **http://127.0.0.1:8765** in your browser. Control reactions, send messages, AI toggles, and more. Set `DASHBOARD_PORT` in `.env` to change the port.

### Commands
Use **/** for slash commands (e.g. `/start`, `/help`). Prefix `!` also works.

- `/start` – React to messages (choose wordlist or all)
- `/stop` – Stop reacting
- `/say` – Make the bot say something
- **Quote** – Right-click a message → Apps → Quote
- `/encrypt`, `/decrypt`, `/brutefernet` – Fernet encryption tools
- `/hug`, `/help`, `/features`, `/lottery`, `/clearmem`, `/update`

### AI mode (Ollama)
Uses local [Ollama](https://ollama.com) with Omega. Run `ollama serve` and `ollama pull aeline/Omega`. AI responds when @mentioned or in AI channels.

### Config
Set these in `.env`:

- `DISCORD_TOKEN`: your bot token
- `EMOJI_NAME` (default `openpaw`): emoji name to look up per-guild
- `EMOJI_ID` (optional): numeric emoji ID to build a PartialEmoji fallback
- `EMOJI_ANIMATED` (optional): `true` if the emoji is animated
- `GUILD_ID` (optional): target guild ID for faster slash sync
- `PUPPET_CHANNEL_ID` (optional): default channel for dashboard "Quick send"
- `AI_FREE_CHANNEL_ID` (optional): channel where AI responds to all messages without @mention
- `OLLAMA_MODEL` (optional, default `aeline/Omega`): Ollama model. Run `ollama pull aeline/Omega`
- `OLLAMA_BASE_URL` (optional, default `http://localhost:11434`): Ollama server URL
- `OLLAMA_STREAM` (optional, default `true`): stream responses
- `SYSTEM_PROMPT` (optional): custom system prompt (single line; use `\n` for newlines)
- `SYSTEM_PROMPT_FILE` (optional): path to file with multiline prompt (e.g. `config/system_prompt.txt`)

### Multi-emoji reactions
Add `config/emojis.json` with an `emojis` array of `{name, id}` objects. The bot picks randomly from the list when reacting. Emoji names also become keywords in wordlist mode.

### GitHub Actions (24/7 hosting)
The workflow `.github/workflows/openpaw-24-7.yml` runs the bot on GitHub. Add these in **Settings → Secrets and variables → Actions**:

**Secrets:**
- `DISCORD_TOKEN` – bot token

Note: The workflow installs Ollama and pulls Omega. For local runs, start `ollama serve` first.

The job restarts every ~6 hours (GitHub limit). State is auto-saved to the repo on exit.

### Project structure
- `config/` – system_prompt.txt, updates.json, emojis.json
- `data/` – reload_state.json, guild exports, wordlists
- `assets/` – images (e.g. ryan-gosling.gif)
- `docs/` – AI context documentation

### !brutefernet
Tries to decrypt Fernet messages. Uses: common passwords + `wordlist.txt` (project root or `data/`) + `/usr/share/dict/words`. Supports SHA256 and PBKDF2 key derivation. Add more passwords to `wordlist.txt`.

Notes:
- The emoji must exist in the server the message is in, or the bot needs "Use External Emojis" permission if the emoji lives elsewhere.
- The bot ignores messages from other bots (prevents loops).
