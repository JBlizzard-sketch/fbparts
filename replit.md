# AutoParts Empire v13 - Telegram Sales Bot

## Overview
This is a sophisticated Telegram bot for auto-parts sales that integrates with Facebook and WhatsApp to automate lead generation and customer engagement for the Kenyan market. The bot uses AI (Groq Llama-3-70B) for intelligent responses and can fall back to template-based responses.

## Recent Changes

### Nov 20, 2025 - Import to Replit Environment Complete
**Migration from Replit Agent to Replit environment successfully completed:**
- ✅ Installed all Node.js and Python dependencies (npm + uv)
- ✅ Installed Playwright browsers (Chromium 141.0.7390.37 + FFMPEG + Headless Shell)
- ✅ Fixed WhatsApp Process.poll() error (changed to returncode for async subprocess)
- ✅ Configured workflow - bot running successfully with Baileys server on port 3000
- ✅ Saved permanent inventory source of truth: **15,440 parts** from Polish Venture in inventory.csv
- ✅ All systems verified operational (Telegram polling, WhatsApp polling, no errors)

### Nov 20, 2025 - EMPIRE v13 COMPLETE UPGRADE
Major migration from Replit Agent to full production environment with Baileys WhatsApp integration:

**WhatsApp Integration (Baileys)**:
- ✅ Full multi-device support with QR code authentication
- ✅ QR codes sent directly to Telegram for easy scanning
- ✅ Session persistence across restarts (named volumes)
- ✅ Real-time message polling every 30 seconds
- ✅ Groq-powered auto-replies with platform context
- ✅ HTTP API for send/receive (/send, /messages, /status endpoints)
- ✅ Pause/resume/remove via inline buttons

**CRUD Operations from Telegram**:
- ✅ **Facebook Groups**: /add_group, /list_groups, /delete_group with ConversationHandler wizards
- ✅ **Facebook Accounts**: /add_fb_account (cookie or email/password), /list_fb_accounts
- ✅ **WhatsApp Numbers**: /add_wa_number with QR code wizard, inline management buttons
- ✅ Zero manual JSON editing required

**Production Deployment**:
- ✅ Multi-stage Docker build (base → dependencies → production)
- ✅ Deterministic builds from pyproject.toml and package-lock.json
- ✅ Named volumes for persistent storage (empire_sessions, empire_data)
- ✅ docker-compose.yml with healthchecks and logging
- ✅ render.yaml for one-click cloud deployment
- ✅ Comprehensive documentation (LOCAL_SETUP.md, RENDER_SETUP.md)

**Code Quality**:
- ✅ All critical issues resolved (architect-approved)
- ✅ WhatsApp auto-replies functional end-to-end
- ✅ Proper error handling and logging
- ✅ Full git diff reviewed and approved

### Nov 20, 2025 - Navigation Improvements
Comprehensive UX overhaul:
- ✅ Persistent Keyboard Menu: Sidebar-style quick access (Home, Leads, Operations, Database, Settings)
- ✅ Enhanced All Menus: Emojis, formatting, contextual stats, status indicators
- ✅ Error Handling: Try/catch protection, graceful recovery, user-friendly messages
- ✅ Zero Dead Ends: Every screen has clear navigation path back
- ✅ NAVIGATION.md: Complete documentation for future agents

### Nov 20, 2025 - Phase 1.3 & 1.4 Complete
Major expansion:
- ✅ Database Schema Expansion: Versioned migrations, 6 tables total
- ✅ All Button Handlers Wired: fb_toggle, fb_force, wa_toggle, wa_list, leads_today, etc.
- ✅ Comprehensive Logging: All actions logged to automation_logs table
- ✅ Background Task Delegation: Force scan, historical scraper async
- ✅ Lead Quality Tracking: hot/warm/cold classification with engagement scores

### Nov 20, 2025 - Initial Replit Setup
- Fixed database schema (renamed 'group' to 'group_url')
- Fixed JSON parsing in wa_numbers.json
- Implemented missing storage.py methods
- Created wa_engine.py implementation
- Configured workflow for Telegram bot
- Installed Playwright with Chromium

## Project Architecture

### Core Files
- **main.py**: Main orchestrator - handles Telegram bot commands, button callbacks, background loops, WhatsApp service startup
- **brain.py**: AI integration using Groq API with fallback to template responses
- **storage.py**: Database management (SQLite), template management, menu handlers
- **fb_engine.py**: Facebook scraping engine using Playwright (scans groups for auto-part requests)
- **wa_engine.py**: WhatsApp integration - Baileys subprocess manager, QR code handling, message polling, auto-replies
- **baileys_client.js**: Node.js WhatsApp client using Baileys library - multi-device, QR generation, HTTP API
- **crud_handlers.py**: Telegram ConversationHandler wizards for managing groups, accounts, WhatsApp numbers

### Configuration Files
- **accounts.json**: Facebook account credentials (auto-created via CRUD)
- **groups.json**: List of Facebook groups to monitor (auto-created via CRUD)
- **wa_numbers.json**: WhatsApp numbers for multi-device (auto-created via CRUD)
- **fb_templates.json**: Auto-generated Facebook reply templates (40% English, 40% Sheng, 20% mix)
- **wa_templates.json**: Auto-generated WhatsApp reply templates
- **package.json**: Node.js dependencies (Baileys, qrcode-terminal, sharp, pino)
- **pyproject.toml**: Python dependencies (python-telegram-bot, playwright, httpx, pandas)

### Deployment Files
- **Dockerfile**: Multi-stage production build (base → dependencies → production)
- **docker-compose.yml**: Local orchestration with named volumes and healthchecks
- **render.yaml**: Cloud deployment configuration for Render
- **.env.example**: Environment variable template
- **LOCAL_SETUP.md**: Complete local development guide
- **RENDER_SETUP.md**: Cloud deployment guide

### Database Schema (v2 - Expanded)
- **schema_meta**: Migration version tracking
- **seen table**: Tracks Facebook posts with quality metrics (post_id, group_url, text, replied, timestamp, engagement_score, lead_quality)
- **inventory table**: Auto-parts inventory (part, price, stock, vehicle, year)
  - **Source of Truth**: inventory.csv with 15,440 parts from Polish Venture
  - Includes: Suspension Parts, Transmission Parts, Brake Parts, Engine Parts, etc.
- **conversations table**: WhatsApp/FB chat thread tracking (id, platform, lead_id, thread_ref, last_message, status, updated_at)
- **sales table**: Revenue and conversion tracking (id, lead_id, amount, currency, parts, payment_method, mpesa_ref, closed_at)
- **accounts_health table**: FB account monitoring (id, platform, account_name, status, last_check, flags, proxy_used)
- **automation_logs table**: Complete audit trail (id, source, action, payload_json, created_at, level)

## Technical Implementation

### WhatsApp Integration Flow
1. User sends `/add_wa_number` to Telegram bot
2. crud_handlers.py starts ConversationHandler wizard
3. wa_engine.py calls baileys_client.js to generate QR code
4. QR code image sent to Telegram for scanning
5. User scans with WhatsApp on phone
6. Baileys saves session to `sessions/whatsapp/{session_name}/`
7. Message polling starts (every 30s via HTTP GET /messages)
8. Incoming messages processed by brain.py (Groq)
9. Replies sent via HTTP POST /send to Baileys
10. All logged to automation_logs table

### Baileys HTTP API Endpoints
- **GET /status**: Client status and message queue length
- **GET /messages?session={name}&limit={n}**: Fetch new messages
- **POST /send**: Send message `{sessionName, jid, message}`

### Docker Multi-Stage Build
1. **Stage 1 (base)**: Python 3.12 slim + Node.js 20 + Chromium system dependencies
2. **Stage 2 (dependencies)**: Install Node packages (`npm ci`), Python packages (`pip install .`), Playwright browsers
3. **Stage 3 (production)**: Copy deps from stage 2, copy app code, create directories, set CMD

### Persistent Storage
- **Named volumes** (not file bind mounts):
  - `empire_sessions:/app/sessions` - WhatsApp/FB authentication
  - `empire_data:/app/data` - Database and JSON files
- Works on fresh clones without pre-existing files

## Setup Instructions

### 1. Required Secrets
Configure in .env file:
- `BOT_TOKEN`: Get from @BotFather on Telegram
- `OWNER_ID`: Your Telegram user ID (get from @userinfobot)
- `GROQ_KEY`: Optional - for AI responses (get from console.groq.com)

### 2. Quick Start
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your secrets
nano .env

# Start with Docker Compose
docker-compose up --build  # first time
docker-compose up -d       # normal start

# View logs
docker-compose logs -f
```

### 3. Configuration via Telegram
All setup done from Telegram - no JSON editing:
- `/add_group` - Add Facebook groups
- `/add_fb_account` - Add Facebook accounts (cookie or email/password)
- `/add_wa_number` - Add WhatsApp numbers (QR wizard)
- Upload CSV inventory via Database menu

## How It Works

### Telegram Control Center
Send `/start` to access main menu:
- **WhatsApp Manager**: Add numbers, view stats, pause/resume, broadcast
- **Live FB Bot**: Start/stop, force scan, rotation stats
- **Templates Manager**: Edit FB & WA templates
- **Leads & Analytics**: View leads, export CSV
- **Historical Scraper**: One-time 3-month scrape
- **Database & CSV**: Upload inventory, view stock
- **FB Accounts**: Manage accounts
- **Settings**: Configure Groq API key, blacklist

### Automated Workflow
1. Bot scans configured Facebook groups every 30 minutes
2. Identifies posts with keywords: "wtb", "need", "looking for", "iso", "part out"
3. Generates authentic Kenyan responses (40% English, 40% Sheng, 20% mix) via Groq
4. Posts replies with website link (autopartspro.shop) and WhatsApp number
5. Tracks all interactions in SQLite database
6. WhatsApp handles inbound customer inquiries with Groq auto-replies
7. Unknown parts forwarded to owner on Telegram

### Response Style
All responses sound like authentic Kenyan car enthusiasts:
- Mix of English and Sheng (Kenyan slang)
- Natural, conversational tone
- Always includes both website and WhatsApp links
- Smart rotation to avoid spam detection

## Dependencies

### Python Packages
- python-telegram-bot==21.5
- playwright==1.56.0
- httpx>=0.28.1
- python-dotenv>=1.2.1
- pandas>=2.3.3

### Node.js Packages
- @whiskeysockets/baileys
- qrcode-terminal
- qrcode
- sharp
- pino

## Deployment

### Local (Replit)
- Workflow runs bot 24/7
- Console output type
- SQLite database persists in workspace
- Sessions in `sessions/` directory

### Local (Docker)
- `docker-compose up --build` for first run
- `docker-compose up -d` for normal start
- Persistent volumes for sessions and data

### Cloud (Render)
- Push to GitHub
- Create Web Service on Render
- Connect repo and set env vars
- Deploy with render.yaml

## Rate Limiting & Safety
- Max 2 actions per account per group per day
- Smart delays (8-20 seconds between replies)
- Account rotation to distribute activity
- Cookie-based login (avoids password issues)
- Blacklist support for problem groups
- Session reuse prevents re-authentication

## User Preferences
- **Deployment**: Local (Replit) and Cloud (Render) support
- **Authentication**: Cookie-based Facebook login preferred
- **Control**: All operations via Telegram inline keyboards
- **No manual editing**: CRUD operations manage all JSON files
- **QR codes in Telegram**: WhatsApp setup without external tools

## Known Status
✅ All major features implemented and working:
- WhatsApp integration with Baileys (full functionality)
- CRUD operations from Telegram (groups, accounts, numbers)
- Groq AI auto-replies (end-to-end tested)
- Docker deployment (multi-stage, deterministic)
- Comprehensive documentation

⏳ Optional future enhancements:
- Advanced analytics dashboard
- Inventory low-stock alerts
- Template inline editing
- Google Sheets sync

## Architecture Decisions
1. **Baileys over other WhatsApp solutions**: User requirement for reliability and multi-device
2. **QR codes in Telegram**: Simplifies setup, no external QR tools needed
3. **ConversationHandler wizards**: Better UX than manual JSON editing
4. **Named volumes**: Works on fresh clones, no file pre-creation needed
5. **Multi-stage Docker**: Optimized images, deterministic builds
6. **HTTP API for Baileys**: Clean Python ↔ Node.js communication
7. **Subprocess management**: Baileys runs alongside Python bot

## Troubleshooting

### Bot Not Starting
- Check BOT_TOKEN and OWNER_ID in .env
- View logs: `docker-compose logs -f`
- Verify no port conflicts (3000 for Baileys)

### WhatsApp QR Not Displaying
- Check Baileys server started: look for "HTTP server running on port 3000"
- Verify Node.js 20 installed
- Check sessions directory writable

### Database Errors
- Delete empire.db to reset (loses history)
- Check JSON files valid (auto-created by CRUD)
- Verify SQLite permissions

### Facebook Scraping Issues
- Update Facebook cookies via /add_fb_account
- Check groups are public or you're a member
- Monitor for rate limiting in logs

### Docker Build Fails
- Ensure 4GB+ memory for Docker
- Verify pyproject.toml and package.json valid
- Check internet connection for dependency downloads

## Contact
All operations via Telegram. Bot runs unattended 24/7.

---

**Status**: Production-ready, architect-approved, fully functional
**Last Updated**: November 20, 2025
**Version**: v13 (Major upgrade complete)
