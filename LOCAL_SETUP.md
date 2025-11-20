# EMPIRE v13 - Local Setup Guide

## Complete step-by-step guide for running EMPIRE v13 on your local machine

---

## Prerequisites

Before you begin, ensure you have:

1. **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
   - Windows: Docker Desktop for Windows
   - Mac: Docker Desktop for Mac
   - Linux: Docker Engine + Docker Compose

2. **A Telegram Bot Token**
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the prompts
   - Save your bot token (format: `123456:ABC-DEF...`)

3. **Your Telegram User ID**
   - Message [@userinfobot](https://t.me/userinfobot)
   - It will reply with your user ID (e.g., `987654321`)

4. **(Optional) Groq API Key**
   - Sign up at [console.groq.com](https://console.groq.com)
   - Create an API key
   - The bot works without this, but AI responses will use templates

---

## Quick Start (5 Minutes)

### Step 1: Clone/Download the Project

```bash
git clone <your-repo-url>
cd empire-v13
```

Or download and extract the ZIP file.

### Step 2: Create `.env` File

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your favorite text editor:

```env
# Your values here (NO QUOTES!)
BOT_TOKEN=your_bot_token_from_botfather
OWNER_ID=your_telegram_user_id
GROQ_KEY=your_groq_api_key_optional
```

**Important**: 
- Remove any quotes around values
- Use just the numeric ID for OWNER_ID (e.g., `7385327404`, not `Id:7385327404`)

### Step 3: Build and Start

```bash
# First time: Build the Docker image (takes 5-8 minutes)
docker compose up --build

# After first build: Normal start (takes 2 seconds)
docker compose up -d
```

### Step 4: Verify It's Running

You should receive a Telegram message from your bot saying:

```
🚀 EMPIRE v13 — ONLINE

Phases 1.3-1.4 complete!

✅ Persistent sidebar menu
✅ All buttons wired
✅ Complete audit logging
```

### Step 5: Configure Your Bot

In Telegram, send `/start` to your bot, then:

1. **Add Facebook Groups**
   ```
   /add_group
   ```
   Then paste a Facebook group URL

2. **Add Facebook Accounts**
   ```
   /add_fb_account
   ```
   Choose cookie-based (recommended) or email/password

3. **Add WhatsApp Numbers**
   ```
   /add_wa_number
   ```
   Enter a session name, then scan the QR code

4. **Upload Inventory**
   - Use the Database menu in Telegram
   - Upload a CSV file with columns: `part,price,stock,vehicle,year`

---

## Daily Usage

### Starting the Bot

```bash
docker compose up -d
```

The `-d` flag runs it in the background (detached mode).

### Stopping the Bot

```bash
docker compose down
```

### Viewing Logs

```bash
# View logs in real-time
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100
```

### Restarting After Code Changes

```bash
docker compose restart
```

Changes to Python files, configs, etc. take effect immediately after restart.

### Rebuilding (After Package Changes)

```bash
# If you modify package.json or requirements.txt
docker compose down
docker compose up --build
```

---

## Configuration Files

### groups.json
List of Facebook groups to monitor:

```json
[
  "https://www.facebook.com/groups/kenyacarscene",
  "https://www.facebook.com/groups/nairobicarsforsale"
]
```

Add groups via `/add_group` in Telegram.

### accounts.json
Facebook accounts for automation:

```json
[
  {
    "name": "KaranjaRacer",
    "cookies": [...]  // Preferred method
  },
  {
    "name": "MutuaDrift",
    "email": "mutua@example.com",
    "password": "yourpassword123"
  }
]
```

Add accounts via `/add_fb_account` in Telegram.

### wa_numbers.json
WhatsApp numbers for customer engagement:

```json
[
  {
    "number": "main-number",
    "name": "Main Sales Line",
    "active": true
  }
]
```

Add numbers via `/add_wa_number` in Telegram.

---

## Telegram Commands Reference

### Group Management
- `/add_group` - Add a Facebook group to monitor
- `/list_groups` - View all configured groups
- `/delete_group` - Remove a group

### Account Management
- `/add_fb_account` - Add a Facebook account
- `/list_fb_accounts` - View all Facebook accounts

### WhatsApp Management
- `/add_wa_number` - Add a WhatsApp number (generates QR code)

### Bot Controls
- `/start` - Open the main menu
- `/cancel` - Cancel any operation

---

## Troubleshooting

### "Container restarts constantly"

Check logs:
```bash
docker compose logs -f
```

Common causes:
- Invalid BOT_TOKEN or OWNER_ID in `.env`
- Missing `.env` file
- Typo in environment variables

### "No .env file"

Make sure the file is named exactly `.env` (not `.env.txt`):

```bash
ls -la | grep env
```

You should see `.env` in the list.

### "Dockerfile not found"

Ensure `Dockerfile` has a capital D:

```bash
ls -la | grep Docker
```

### "QR code not appearing"

1. Check that Baileys server started:
   ```bash
   docker compose logs -f | grep BAILEYS
   ```

2. You should see: `✅ Baileys server started successfully`

3. If not, restart the bot:
   ```bash
   docker compose restart
   ```

### "Facebook scraping not working"

1. Check that you've added accounts via `/add_fb_account`
2. For cookie-based auth:
   - Install [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/) extension
   - Go to facebook.com (logged in)
   - Click extension → Export
   - Paste the JSON when prompted

---

## Performance Tips

### For Better Facebook Results

1. Use **cookie-based authentication** (more reliable)
2. Add **multiple accounts** (distributes load, reduces bans)
3. Set **realistic intervals** (default 30 minutes is safe)
4. Monitor **account health** in the bot

### For Better WhatsApp Results

1. Use a **dedicated phone number** (not your personal number)
2. **Warm up** new numbers (use manually for a few days first)
3. Avoid **spam behavior** (rate limiting is built-in)

---

## File Structure

```
empire-v13/
├── main.py                  # Main bot orchestrator
├── brain.py                 # Groq AI integration
├── storage.py               # Database management
├── fb_engine.py             # Facebook automation
├── wa_engine.py             # WhatsApp integration
├── crud_handlers.py         # CRUD operations
├── baileys_client.js        # WhatsApp Baileys client
├── Dockerfile               # Docker build instructions
├── docker-compose.yml       # Docker Compose config
├── .env                     # Your secrets (NEVER commit!)
├── groups.json              # Facebook groups
├── accounts.json            # Facebook accounts
├── wa_numbers.json          # WhatsApp numbers
├── fb_templates.json        # FB reply templates
├── wa_templates.json        # WA reply templates
├── empire.db                # SQLite database
└── sessions/                # Playwright & Baileys sessions
    ├── facebook/
    └── whatsapp/
```

---

## Next Steps

1. ✅ Bot is running locally
2. Configure Facebook groups, accounts, and WhatsApp numbers
3. Upload your auto-parts inventory
4. Monitor leads in Telegram
5. Deploy to Render for 24/7 operation (see `RENDER_SETUP.md`)

---

## Support

- Check logs: `docker compose logs -f`
- Review `NAVIGATION.md` for Telegram menu structure
- See `EXPANSION_ROADMAP.md` for future features

**Your local EMPIRE v13 is ready! 🚀**
