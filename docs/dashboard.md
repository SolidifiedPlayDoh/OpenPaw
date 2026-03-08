# Dashboard Module - Web Control Panel

## Overview
A localhost web server (aiohttp) that provides a control panel for the bot. Runs alongside the bot in the same process. Default port 8765.

## API Endpoints

### GET /api/status
Returns JSON: reaction_enabled, reaction_mode, default_channel_id, ai_enabled, ai_channel_id, ai_mention_enabled, ai_context_files (list of doc filenames), fake_brute_pending (channels with pending fake decrypts).

### GET /api/channels
Returns list of text channels the bot can see: id, name, guild name. Sorted by guild then channel name.

### POST /api/start
Body: { mode: "all" | "wordlist" }. Starts reactions with the given mode.

### POST /api/stop
Stops the reaction system.

### POST /api/say
Body: { channel_id, message }. Sends a message to the specified channel.

### POST /api/ai_toggle
Body: { enabled: bool, channel_id }. Enables or disables AI for a specific channel.

### POST /api/ai_mention_toggle
Body: { enabled: bool }. Enables or disables AI responses when the bot is @mentioned.

### POST /api/ai_context
Body: { files: ["bot.md", "brute_fernet.md", ...] }. Sets which documentation files the AI can read. These are markdown docs with descriptions, not raw code.

### POST /api/complete_fake_brute
Body: { channel_id, decoded_text }. Completes a pending fake brute-force session. The bot edits the Discord message to show the user-provided "decrypted" result.

## UI Sections
- Status indicator (reacting/stopped)
- Start/Stop reaction buttons
- Quick send (to default channel)
- Send message (channel picker + input)
- AI Mode (channel select + enable/disable)
- AI when @mentioned (enable/disable)
- AI code context (checkboxes for which doc files to include)
- Decryption result (for fake brute - only visible when pending)

## Styling
Dark theme with accent color. Uses Outfit and JetBrains Mono fonts. Cards for each section. Toast notifications for feedback.
