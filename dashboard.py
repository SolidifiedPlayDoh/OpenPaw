"""
Web dashboard for the OpenPaw bot. Runs on localhost alongside the bot.
"""
import os
import discord
from aiohttp import web

DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8765"))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenPaw Bot</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0d0d0f;
      --surface: #16161a;
      --surface-hover: #1e1e24;
      --border: #2a2a32;
      --text: #e8e6e3;
      --text-muted: #8b8685;
      --accent: #e8b923;
      --accent-dim: #b8921a;
      --success: #4ade80;
      --danger: #f87171;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Outfit', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }
    .container { max-width: 720px; margin: 0 auto; }
    h1 {
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .subtitle { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 2rem; }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
    }
    .card h2 {
      font-size: 0.85rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }
    .status-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9rem;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      animation: pulse 2s infinite;
    }
    .status-dot.off { background: var(--text-muted); animation: none; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .btn-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    button {
      font-family: 'Outfit', sans-serif;
      font-weight: 600;
      padding: 0.6rem 1rem;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.15s;
    }
    button:hover { transform: translateY(-1px); }
    button:active { transform: translateY(0); }
    .btn-primary {
      background: var(--accent);
      color: var(--bg);
    }
    .btn-primary:hover { background: var(--accent-dim); }
    .btn-secondary {
      background: var(--surface-hover);
      color: var(--text);
      border: 1px solid var(--border);
    }
    .btn-secondary:hover { background: var(--border); }
    .btn-danger { background: #7f1d1d; color: #fecaca; }
    .btn-danger:hover { background: #991b1b; }
    input, select {
      font-family: 'JetBrains Mono', monospace;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.6rem 0.9rem;
      color: var(--text);
      font-size: 0.9rem;
      width: 100%;
      margin-bottom: 0.75rem;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--accent);
    }
    textarea {
      font-family: 'JetBrains Mono', monospace;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.6rem 0.9rem;
      color: var(--text);
      font-size: 0.9rem;
      width: 100%;
      margin-bottom: 0.75rem;
    }
    label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem; }
    .toast {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      padding: 0.75rem 1.25rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.9rem;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.2s;
      z-index: 100;
    }
    .toast.show { opacity: 1; transform: translateY(0); }
    .toast.error { border-color: var(--danger); }
  </style>
</head>
<body>
  <div class="container">
    <h1>OpenPaw Bot</h1>
    <p class="subtitle">Control panel</p>

    <div class="card">
      <h2>Status</h2>
      <div class="status-row">
        <span class="status-dot" id="statusDot"></span>
        <span id="statusText">Loading...</span>
      </div>
    </div>

    <div class="card">
      <h2>Reactions</h2>
      <div class="btn-row">
        <button class="btn-primary" onclick="api('start', {mode: 'all'})">Start (all)</button>
        <button class="btn-primary" onclick="api('start', {mode: 'wordlist'})">Start (wordlist)</button>
        <button class="btn-danger" onclick="api('stop')">Stop</button>
      </div>
    </div>

    <div class="card" id="quickSendCard" style="display:none">
      <h2>Quick send</h2>
      <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">Sends to your default channel (PUPPET_CHANNEL_ID)</p>
      <label>Message</label>
      <input type="text" id="quickSayInput" placeholder="Type something for the bot to say...">
      <button class="btn-primary" onclick="quickSend()">Send</button>
    </div>

    <div class="card">
      <h2>Send message</h2>
      <label>Channel</label>
      <select id="channelSelect">
        <option value="">Loading channels...</option>
      </select>
      <label>Message</label>
      <input type="text" id="sayInput" placeholder="Type something for the bot to say...">
      <button class="btn-primary" onclick="sendMessage()">Send</button>
    </div>

    <div class="card" id="fakeBruteCard" style="display:none">
      <h2>Decryption result</h2>
      <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;" id="fakeBruteDesc">Waiting for input...</p>
      <label>Channel</label>
      <select id="fakeBruteChannelSelect">
        <option value="">No pending</option>
      </select>
      <label>Decoded text</label>
      <textarea id="fakeBruteDecoded" rows="4" placeholder="Enter the decrypted result..." style="resize:vertical; font-family: inherit;"></textarea>
      <button class="btn-primary" onclick="completeFakeBrute()">Complete</button>
    </div>

    <div class="card">
      <h2>AI Mode</h2>
      <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">Messages in the selected channel get AI responses. Use !clearmem to clear history.</p>
      <label>Channel</label>
      <select id="aiChannelSelect">
        <option value="">Loading channels...</option>
      </select>
      <div class="btn-row" style="margin-top: 0.5rem;">
        <button class="btn-primary" id="aiOnBtn" onclick="aiToggle(true)">Enable AI</button>
        <button class="btn-danger" id="aiOffBtn" onclick="aiToggle(false)">Disable AI</button>
      </div>
      <p id="aiStatus" style="font-size:0.85rem; color: var(--text-muted); margin-top: 0.5rem;"></p>
    </div>

    <div class="card">
      <h2>AI when @mentioned</h2>
      <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">When someone @mentions the bot, it responds with AI. Works in any channel.</p>
      <div class="btn-row">
        <button class="btn-primary" id="mentionOnBtn" onclick="aiMentionToggle(true)">Enable</button>
        <button class="btn-danger" id="mentionOffBtn" onclick="aiMentionToggle(false)">Disable</button>
      </div>
      <p id="mentionStatus" style="font-size:0.85rem; color: var(--text-muted); margin-top: 0.5rem;"></p>
    </div>

    <div class="card">
      <h2>AI documentation context</h2>
      <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">Which docs the AI can read (descriptions only, no raw code). Safer from prompt injection.</p>
      <div id="contextFilesList" style="display:flex; flex-wrap:wrap; gap:0.5rem 1rem;">
        <label style="display:flex; align-items:center; gap:0.35rem; cursor:pointer; margin:0;"><input type="checkbox" data-file="bot.md"> bot.md</label>
        <label style="display:flex; align-items:center; gap:0.35rem; cursor:pointer; margin:0;"><input type="checkbox" data-file="brute_fernet.md"> brute_fernet.md</label>
        <label style="display:flex; align-items:center; gap:0.35rem; cursor:pointer; margin:0;"><input type="checkbox" data-file="dashboard.md"> dashboard.md</label>
        <label style="display:flex; align-items:center; gap:0.35rem; cursor:pointer; margin:0;"><input type="checkbox" data-file="quotes.md"> quotes.md</label>
      </div>
      <button class="btn-secondary" style="margin-top:0.5rem" onclick="saveContextFiles()">Save</button>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    const channelSelect = document.getElementById('channelSelect');

    async function api(endpoint, body = {}) {
      try {
        const res = await fetch('/api/' + endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || res.statusText);
        showToast('Done');
        refreshStatus();
        return data;
      } catch (e) {
        showToast(e.message, true);
      }
    }

    async function refreshStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('statusText').textContent =
          data.reaction_enabled
            ? `Reacting (${data.reaction_mode})`
            : 'Stopped';
        document.getElementById('statusDot').className =
          data.reaction_enabled ? 'status-dot' : 'status-dot off';
        const qc = document.getElementById('quickSendCard');
        if (data.default_channel_id) {
          qc.style.display = 'block';
          qc.dataset.channelId = String(data.default_channel_id);
        } else {
          qc.style.display = 'none';
        }
        const aiStatus = document.getElementById('aiStatus');
        if (data.ai_enabled && data.ai_channel_id) {
          aiStatus.textContent = 'AI is ON in channel ' + data.ai_channel_id;
        } else {
          aiStatus.textContent = 'AI is OFF';
        }
        const mentionStatus = document.getElementById('mentionStatus');
        mentionStatus.textContent = data.ai_mention_enabled ? 'Responding when @mentioned' : 'OFF';
        const files = data.ai_context_files || [];
        document.querySelectorAll('#contextFilesList input[data-file]').forEach(cb => {
          cb.checked = files.includes(cb.dataset.file);
        });
        const fbCard = document.getElementById('fakeBruteCard');
        const pending = data.fake_brute_pending || [];
        if (pending.length > 0) {
          fbCard.style.display = 'block';
          document.getElementById('fakeBruteDesc').textContent =
            'Decryption in progress. Enter the result below to complete.';
          const sel = document.getElementById('fakeBruteChannelSelect');
          sel.innerHTML = pending.map(p =>
            `<option value="${p.channel_id}">${p.guild_name} › #${p.channel_name}</option>`
          ).join('');
        } else {
          fbCard.style.display = 'none';
        }
      } catch {
        document.getElementById('statusText').textContent = 'Offline';
        document.getElementById('statusDot').className = 'status-dot off';
      }
    }

    async function quickSend() {
      const msg = document.getElementById('quickSayInput').value.trim();
      const channelId = document.getElementById('quickSendCard').dataset.channelId;
      if (!channelId || !msg) {
        showToast('Enter a message', true);
        return;
      }
      await api('say', { channel_id: channelId, message: msg });
      document.getElementById('quickSayInput').value = '';
    }

    async function loadChannels() {
      try {
        const res = await fetch('/api/channels');
        const channels = await res.json();
        const opts = channels.map(c => `<option value="${c.id}">${c.guild} › ${c.name}</option>`).join('');
        channelSelect.innerHTML = opts || '<option value="">No channels</option>';
        document.getElementById('aiChannelSelect').innerHTML = opts || '<option value="">No channels</option>';
      } catch {
        channelSelect.innerHTML = '<option value="">Failed to load</option>';
        document.getElementById('aiChannelSelect').innerHTML = '<option value="">Failed to load</option>';
      }
    }

    async function sendMessage() {
      const channelId = channelSelect.value;
      const msg = document.getElementById('sayInput').value.trim();
      if (!channelId || !msg) {
        showToast('Pick a channel and enter a message', true);
        return;
      }
      await api('say', { channel_id: channelId, message: msg });
      document.getElementById('sayInput').value = '';
    }

    async function aiToggle(enabled) {
      const channelId = document.getElementById('aiChannelSelect').value;
      if (enabled && !channelId) {
        showToast('Select a channel first', true);
        return;
      }
      await api('ai_toggle', { enabled, channel_id: channelId || null });
    }

    async function aiMentionToggle(enabled) {
      await api('ai_mention_toggle', { enabled });
    }

    async function saveContextFiles() {
      const files = [];
      document.querySelectorAll('#contextFilesList input[data-file]:checked').forEach(cb => {
        files.push(cb.dataset.file);
      });
      await api('ai_context', { files });
    }

    async function completeFakeBrute() {
      const channelId = document.getElementById('fakeBruteChannelSelect').value;
      const decodedText = document.getElementById('fakeBruteDecoded').value.trim();
      if (!channelId || !decodedText) {
        showToast('Select a channel and enter decoded text', true);
        return;
      }
      try {
        const res = await fetch('/api/complete_fake_brute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel_id: channelId, decoded_text: decodedText })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || res.statusText);
        showToast('Done');
        document.getElementById('fakeBruteDecoded').value = '';
        refreshStatus();
      } catch (e) {
        showToast(e.message, true);
      }
    }

    function showToast(msg, isError = false) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.className = 'toast show' + (isError ? ' error' : '');
      setTimeout(() => t.classList.remove('show'), 2500);
    }

    loadChannels();
    refreshStatus();
    setInterval(refreshStatus, 5000);
  </script>
</body>
</html>
"""


def create_app(bot, callbacks):
    """Create aiohttp app with bot controls."""
    app = web.Application()

    async def status(_):
        state = getattr(bot, "bot_state", {})
        ai = getattr(bot, "ai_state", {})
        default_ch = getattr(bot, "puppet_channel_id", None)
        default_ch = int(default_ch) if default_ch and str(default_ch).strip() else None
        pending = getattr(bot, "fake_brute_pending", {})
        pending_list = []
        for cid, data in pending.items():
            ch = bot.get_channel(cid)
            pending_list.append({
                "channel_id": str(cid),
                "channel_name": ch.name if ch else str(cid),
                "guild_name": ch.guild.name if ch and ch.guild else "DM",
            })
        return web.json_response({
            "reaction_enabled": state.get("reaction_enabled", False),
            "reaction_mode": state.get("reaction_mode", "wordlist"),
            "default_channel_id": default_ch,
            "ai_enabled": ai.get("enabled", False),
            "ai_channel_id": ai.get("channel_id"),
            "ai_mention_enabled": ai.get("mention_enabled", False),
            "ai_context_files": ai.get("context_files", []),
            "fake_brute_pending": pending_list,
        })

    async def channels(_):
        chans = []
        for ch in bot.get_all_channels():
            if isinstance(ch, discord.TextChannel):
                chans.append({
                    "id": str(ch.id),
                    "name": ch.name,
                    "guild": ch.guild.name if ch.guild else "DM",
                })
        chans.sort(key=lambda c: (c["guild"], c["name"]))
        return web.json_response(chans)

    async def start(request):
        data = await request.json() if request.content_length else {}
        mode = (data.get("mode") or "wordlist").lower()
        if mode not in ("all", "wordlist"):
            return web.json_response({"error": "Invalid mode"}, status=400)
        await callbacks["start"](mode)
        return web.json_response({"ok": True})

    async def stop(request):
        await callbacks["stop"]()
        return web.json_response({"ok": True})

    async def say(request):
        data = await request.json() if request.content_length else {}
        channel_id = data.get("channel_id")
        message = data.get("message", "").strip()
        if not channel_id or not message:
            return web.json_response({"error": "channel_id and message required"}, status=400)
        try:
            cid = int(str(channel_id))
            await callbacks["say"](cid, message)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"ok": True})

    async def ai_toggle(request):
        data = await request.json() if request.content_length else {}
        enabled = bool(data.get("enabled", False))
        channel_id = data.get("channel_id")
        if enabled and not channel_id:
            return web.json_response({"error": "Select a channel when enabling AI"}, status=400)
        try:
            cid = int(str(channel_id)) if channel_id else None
            await callbacks["ai_toggle"](enabled, cid)
        except (ValueError, TypeError) as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"ok": True})

    async def ai_mention_toggle(request):
        data = await request.json() if request.content_length else {}
        enabled = bool(data.get("enabled", False))
        await callbacks["ai_mention_toggle"](enabled)
        return web.json_response({"ok": True})

    async def ai_context(request):
        data = await request.json() if request.content_length else {}
        files = data.get("files")
        if files is not None and not isinstance(files, list):
            files = [f for f in str(files).split(",") if f.strip()]
        await callbacks["ai_context"](files or [])
        return web.json_response({"ok": True})

    async def complete_fake_brute(request):
        data = await request.json() if request.content_length else {}
        channel_id = data.get("channel_id")
        decoded_text = (data.get("decoded_text") or "").strip()
        if not channel_id or not decoded_text:
            return web.json_response({"error": "channel_id and decoded_text required"}, status=400)
        try:
            cid = int(str(channel_id))
            await callbacks["complete_fake_brute"](cid, decoded_text)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"ok": True})

    async def index(_):
        return web.Response(text=HTML, content_type="text/html")

    app.router.add_get("/", index)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/channels", channels)
    app.router.add_post("/api/start", start)
    app.router.add_post("/api/stop", stop)
    app.router.add_post("/api/say", say)
    app.router.add_post("/api/ai_toggle", ai_toggle)
    app.router.add_post("/api/ai_mention_toggle", ai_mention_toggle)
    app.router.add_post("/api/ai_context", ai_context)
    app.router.add_post("/api/complete_fake_brute", complete_fake_brute)

    return app


async def start_dashboard(bot, callbacks, port=DASHBOARD_PORT):
    """Start the dashboard server in the bot's event loop."""
    app = create_app(bot, callbacks)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    print(f"Dashboard: http://127.0.0.1:{port}")
