# EMPIRE v13 - Navigation System Documentation
**Last Updated: November 20, 2025**

## Overview
EMPIRE v13 uses a hub-and-spoke navigation pattern with persistent keyboard menu and comprehensive inline button navigation. All screens are designed to prevent dead ends and provide clear navigation paths.

## Navigation Architecture

### Persistent Menu (Sidebar-Style)
A persistent keyboard menu is always visible at the bottom of the chat, providing quick access to major sections:
- 🏠 Home - Return to main dashboard
- 📊 Leads - Jump to leads dashboard
- ⚙️ Operations - Access operations center (FB, WA, Historical)
- 📁 Database - Database and inventory management
- 🔧 Settings - Bot configuration

### Main Menu (Hub)
The main menu serves as the central hub with 8 modules:
- 📘 Live FB Bot - Facebook automation controls
- 💬 WhatsApp - WhatsApp management (requires Phase 1.1)
- 📝 Templates - Response template management
- 📊 Leads - Lead tracking and analytics
- ⏳ Historical Scan - 3-month historical scraper
- 📁 Database - Inventory and CSV management
- 👤 FB Accounts - Facebook account management
- ⚙️ Settings - API keys and configuration

## Complete Navigation Map

### 1. Live FB Bot (fb_menu)
```
📘 LIVE FB BOT
├─ ▶️/⏸️ Toggle Scan (fb_toggle)
├─ ⚡ Force Scan Now (fb_force)
└─ 🏠 Main Menu (main_menu)
```

**Actions:**
- `fb_toggle`: Start/stop automated group monitoring
- `fb_force`: Immediate scan regardless of active state
- Logs all actions to automation_logs table

### 2. WhatsApp Manager (wa_menu)
```
💬 WHATSAPP MANAGER
├─ 📱 View Numbers (wa_list)
│  └─ ◀️ Back to WhatsApp (wa_menu)
├─ ▶️/⏸️ Toggle Service (wa_toggle)
└─ 🏠 Main Menu (main_menu)
```

**Actions:**
- `wa_list`: Display all configured WhatsApp numbers with status
- `wa_toggle`: Start/stop WhatsApp service
- Note: Full integration requires Baileys setup (Phase 1.1)

### 3. Templates Manager (templates_menu)
```
📝 TEMPLATES MANAGER
├─ 📘 FB Templates (edit_fb)
│  └─ ◀️ Back to Templates (templates_menu)
├─ 💬 WA Templates (edit_wa)
│  └─ ◀️ Back to Templates (templates_menu)
└─ 🏠 Main Menu (main_menu)
```

**Template Viewing:**
- Shows first 5 templates with preview
- Displays total count and tone guidelines (40% English, 40% Sheng, 20% mix)
- Edit via JSON files (fb_templates.json, wa_templates.json)

### 4. Leads & Analytics (leads_menu)
```
📊 LEADS & ANALYTICS
├─ 📅 Today's Leads (leads_today)
│  ├─ 📥 Export CSV (leads_export)
│  └─ ◀️ Back to Leads (leads_menu)
├─ 📥 Export All CSV (leads_export)
└─ 🏠 Main Menu (main_menu)
```

**Features:**
- Real-time stats: Today, All Time, Replied, Pending
- Lead quality breakdown: 🔥 Hot, 🟡 Warm, ❄️ Cold
- Paginated display (shows 5, indicates total)
- CSV export includes all metadata

### 5. Historical Scraper (hist_menu)
```
⏳ HISTORICAL SCRAPER
├─ ▶️/⏸️ Start/Stop Scrape (hist_start)
├─ 📊 View Progress (hist_progress)
│  ├─ 🔄 Refresh (hist_progress)
│  └─ ◀️ Back (hist_menu)
└─ 🏠 Main Menu (main_menu)
```

**Progress Tracking:**
- Real-time status updates
- Current group being scraped
- Total posts scraped counter
- Background task delegation

### 6. Database & CSV (db_menu)
```
📁 DATABASE MANAGER
├─ 📦 View Inventory (view_inventory)
│  ├─ 📤 Upload New CSV (upload_csv)
│  └─ ◀️ Back to Database (db_menu)
├─ 📤 Upload CSV (upload_csv)
│  └─ ◀️ Back to Database (db_menu)
└─ 🏠 Main Menu (main_menu)
```

**Inventory Display:**
- Shows first 15 parts
- Formatted with prices (KES), stock, vehicle info
- Empty state prompts CSV upload
- Required columns: part, price, stock, vehicle, year

### 7. FB Accounts (fb_accounts)
```
👤 FB ACCOUNTS MANAGER
├─ Shows first 3 accounts
├─ Displays email or "Cookie-based"
└─ 🏠 Main Menu (main_menu)
```

**Account Management:**
- Configured via accounts.json
- Supports email/password or cookie-based login
- Shows account count and configuration instructions

### 8. Settings (settings_menu)
```
⚙️ SETTINGS
├─ 🧠 Groq API (settings_groq)
│  └─ ◀️ Back to Settings (settings_menu)
└─ 🏠 Main Menu (main_menu)
```

**Configuration Status:**
- Groq AI: Shows ✅/❌ status
- Bot Token: ✅ (always set)
- Owner ID: ✅ (always set)

## Navigation Principles

### 1. No Dead Ends
Every screen has a clear path back:
- Submenus always have ◀️ Back button
- Detail views return to parent menu
- All paths lead to main menu

### 2. Consistent Icons
- 🏠 Home/Main Menu
- ◀️ Back to previous screen
- ▶️/⏸️ Toggle actions (Start/Stop)
- 📊 Analytics/Progress
- 📥 Export/Download
- 📤 Upload
- ⚡ Immediate action
- 🔄 Refresh

### 3. Contextual Information
Every menu shows relevant stats:
- Current status (ACTIVE/PAUSED/RUNNING/IDLE)
- Counts (accounts, groups, numbers, parts, leads)
- Quality indicators (🟢 Active, ⚪ Inactive)

### 4. Action Logging
All button clicks logged to automation_logs:
- Source: 'navigation', 'fb_engine', 'wa_engine', 'storage'
- Action: button name or operation
- Payload: relevant metadata

## Persistent Menu Quick Actions

### 🏠 Home
Returns to main dashboard with full stats

### 📊 Leads
Direct jump to leads dashboard showing:
- Today's count
- Replied vs Pending
- Quick access to today's leads and export

### ⚙️ Operations
Operations center showing:
- FB Scanning status
- WA Service status
- Historical Scan status
- Links to all operation modules

### 📁 Database
Database manager showing:
- Inventory count
- Table list
- Quick access to view and upload

### 🔧 Settings
Settings overview showing:
- Groq AI status
- Bot configuration
- API key management

## For Future Agents

### Adding New Menus
1. Create `show_*_menu` method in appropriate module (storage.py, fb_engine.py, wa_engine.py)
2. Add callback_data handler in main.py `button()` function
3. Ensure every screen has a back button
4. Add action logging for user interactions
5. Include contextual stats/information
6. Use consistent emoji icons

### Navigation Best Practices
1. Always include parent context in back buttons ("Back to X")
2. Show status indicators (🟢/⚪ for active/inactive)
3. Paginate long lists (show 5-15 items, indicate total)
4. Provide empty states with clear instructions
5. Log all actions for audit trail
6. Use async background tasks for long operations

### Testing Navigation
Test each path:
1. Main menu → All 8 modules → Back
2. Persistent menu → All 5 quick actions
3. Verify all buttons lead somewhere (no unhandled callbacks)
4. Check empty states (no inventory, no leads, etc.)
5. Verify status updates after actions

## Button Callback Reference

### Main Navigation
- `main_menu` - Main dashboard
- `fb_menu` - Facebook bot menu
- `wa_menu` - WhatsApp menu
- `templates_menu` - Templates manager
- `leads_menu` - Leads & analytics
- `hist_menu` - Historical scraper
- `db_menu` - Database manager
- `fb_accounts` - FB accounts
- `settings_menu` - Settings

### Actions
- `fb_toggle` - Toggle FB scanning
- `fb_force` - Force immediate scan
- `wa_toggle` - Toggle WA service
- `wa_list` - List WA numbers
- `leads_today` - Today's leads
- `leads_export` - Export leads CSV
- `hist_start` - Start historical scrape
- `hist_progress` - View scrape progress
- `upload_csv` - Prompt CSV upload
- `view_inventory` - Show inventory
- `edit_fb` - View FB templates
- `edit_wa` - View WA templates
- `settings_groq` - Groq API settings

## Architecture Compliance

This navigation system follows the architect's guidance:
✅ Hub-and-spoke pattern with central dispatcher
✅ Persistent menu for "sidebar" effect
✅ Every submenu has explicit next actions
✅ No dead ends (all screens navigable)
✅ Lightweight keyboards (≤8 buttons)
✅ Comprehensive logging
✅ State validation in central dispatcher
✅ Documented navigation flows

## Status
🟢 **FULLY OPERATIONAL**
- All buttons wired and tested
- Persistent menu active
- Navigation logging enabled
- Zero dead ends
- Consistent UX throughout
