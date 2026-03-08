# Bot Module - Main Discord Bot

## Overview
The main bot module runs a Discord bot with prefix commands, reactions, AI chat, encryption tools, and voice channel following.

## Commands

### !start
Starts the reaction system. Two modes:
- **wordlist**: Reacts only to messages containing keywords (openpaw, pawsy, paw) or the custom emoji
- **all**: Reacts to every message in the channel

The bot finds the guild emoji by name (configurable via env) or by ID. When starting in "all" mode, it immediately reacts to the most recent non-bot message.

### !stop
Stops reacting. Removes the emoji from the currently reacted message and clears the tracking state.

### !help
Lists all commands in an embed. Uses custom descriptions for commands that have extra options.

### !quote
Reply to a message first, then run this. Fetches the replied message's author avatar, content, and timestamp. Creates a poster-style quote card image (via the quotes module) and sends it as a PNG. Content is truncated to 500 chars. Handles embeds and attachments in the message.

### !encrypt
Encrypts text with Fernet. Usage: the last word is the key, everything before is the text. Uses SHA256 key derivation. Outputs the encrypted string in a code block.

### !decrypt
Decrypts a Fernet string when you know the key. Same parsing: last word is key, rest is the encrypted string. Outputs decrypted text (truncated to 500 chars) or an error if the key is wrong.

### !brutefernet
Attempts to brute-force decrypt Fernet messages. Two modes:
- **Normal**: Tries common passwords and system wordlists (SHA256 only). Shows progress updates. Uses multiprocessing with Zeta-force chunking (searches from both ends of the list).
- **-a flag (pretend mode)**: Shows fake progress, waits for the user to submit the "decrypted" result via the web dashboard. Used for demonstrations - never actually decrypts.

Progress is shown as phase (common/wordlist), current/total, and last password tried. On success shows the decrypted text and password used.

### !clearmem
Clears the AI chat history for the current channel.

### !say
Makes the bot say something. Can target a specific channel: first argument as channel ID, rest as message. Otherwise sends to the current channel.

## AI Mode
- **Channel mode**: When enabled for a channel, all non-command messages get AI responses. Uses Groq API (Llama 4 Scout, same as vision_bot). Chat history is kept per channel (last 20 messages).
- **Mention mode**: When enabled, @mentioning the bot in any channel triggers an AI response. Same behavior as channel mode.
- **Vision**: When users send images with their message, the AI can analyze them (same model as vision_bot).
- The AI has access to documentation files (not raw code) to answer "how does X work?" questions. It is instructed to NEVER output actual code - only describe behavior in plain language.

## Reactions
When reaction mode is on, the bot tracks the "last reacted message" and moves its emoji to the newest matching message. In wordlist mode, if a new message doesn't match keywords, it removes the reaction from the previous message. The emoji is resolved from the guild by name or from env-configured ID.

## Voice
The bot automatically joins voice channels when a member joins, follows them if they switch channels, and leaves when the channel is empty. It announces in the guild's system channel when it joins.

## Dashboard Integration
The bot starts a local web dashboard (aiohttp) that provides: start/stop reactions, send messages, AI toggles, fake brute-force completion, and context file selection. Callbacks are passed to the dashboard for these actions.
