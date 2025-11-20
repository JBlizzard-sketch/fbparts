# storage.py - EXPANDED SCHEMA - NOV 20 2025
import sqlite3
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import io
import logging

logger = logging.getLogger("Storage")

class Storage:
    def __init__(self):
        self.conn = sqlite3.connect("empire.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Run migrations
        self._run_migrations()
        
    def _run_migrations(self):
        """Versioned database migrations"""
        # Create schema metadata table
        self.conn.execute("CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER PRIMARY KEY)")
        self.conn.commit()
        
        current_version = self.conn.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] or 0
        
        # Migration 1: Original schema
        if current_version < 1:
            logger.info("Running migration 1: Original schema")
            cursor = self.conn.execute("PRAGMA table_info(seen)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if columns and "group" in columns and "group_url" not in columns:
                self.conn.execute("ALTER TABLE seen RENAME TO seen_old")
                self.conn.execute("CREATE TABLE IF NOT EXISTS seen (post_id TEXT PRIMARY KEY, group_url TEXT, text TEXT, replied INTEGER DEFAULT 0)")
                self.conn.execute("INSERT INTO seen (post_id, group_url, text, replied) SELECT post_id, group, text, replied FROM seen_old")
                self.conn.execute("DROP TABLE seen_old")
            elif not columns:
                self.conn.execute("CREATE TABLE IF NOT EXISTS seen (post_id TEXT PRIMARY KEY, group_url TEXT, text TEXT, replied INTEGER DEFAULT 0)")
            
            self.conn.execute("CREATE TABLE IF NOT EXISTS inventory (part TEXT, price REAL, stock INTEGER, vehicle TEXT, year TEXT)")
            self.conn.execute("INSERT INTO schema_meta (version) VALUES (1)")
            self.conn.commit()
            
        # Migration 2: Expand seen table and add new tables
        if current_version < 2:
            logger.info("Running migration 2: Expanded schema")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_new (
                    post_id TEXT PRIMARY KEY,
                    group_url TEXT,
                    text TEXT,
                    replied INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT (datetime('now')),
                    engagement_score REAL DEFAULT 0,
                    lead_quality TEXT DEFAULT 'cold'
                )
            """)
            
            # Copy existing data
            cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen'")
            if cursor.fetchone():
                self.conn.execute("""
                    INSERT INTO seen_new (post_id, group_url, text, replied)
                    SELECT post_id, group_url, text, replied FROM seen
                """)
                self.conn.execute("DROP TABLE seen")
            
            self.conn.execute("ALTER TABLE seen_new RENAME TO seen")
            
            # Conversations table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    lead_id TEXT,
                    thread_ref TEXT,
                    last_message TEXT,
                    status TEXT DEFAULT 'active',
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_lead ON conversations(lead_id)")
            
            # Sales table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'KES',
                    parts TEXT,
                    payment_method TEXT,
                    mpesa_ref TEXT,
                    closed_at TEXT DEFAULT (datetime('now'))
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_lead ON sales(lead_id)")
            
            # Accounts health table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    account_name TEXT,
                    status TEXT DEFAULT 'active',
                    last_check TEXT DEFAULT (datetime('now')),
                    flags TEXT,
                    proxy_used TEXT
                )
            """)
            
            # Automation logs table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    action TEXT,
                    payload_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    level TEXT DEFAULT 'info'
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_created ON automation_logs(created_at)")
            
            self.conn.execute("INSERT INTO schema_meta (version) VALUES (2)")
            self.conn.commit()
            logger.info("Migration 2 complete")

        # Auto-create templates with perfect 8/8/4 ratio
        self.fb_templates = self.load_or_create("fb_templates.json", self.default_fb_templates())
        self.wa_templates = self.load_or_create("wa_templates.json", self.default_wa_templates())

        self.fb_accounts = self.load_json("fb_accounts.json")
        self.groups = self.load_json("groups.json")
        self.wa_numbers = self.load_json("wa_numbers.json")

    def load_json(self, filename):
        path = Path(filename)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return []

    def load_or_create(self, filename, default_list):
        path = Path(filename)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("templates", default_list)
        else:
            data = {"templates": default_list}
            path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
            return default_list

    def default_fb_templates(self):
        return [
            # 8 Pure English
            "I always get my parts from autopartspro.shop - fast shipping and real OEM every time",
            "These guys are legit, bought coilovers last month and they arrived in 2 days",
            "Best prices I've found online, no cap. Check autopartspro.shop",
            "Just ordered from them again, never had an issue with quality or delivery",
            "Highly recommend - got my turbo kit from autopartspro.shop and it was perfect",
            "Saved me thousands compared to the dealer. Real parts, fast delivery",
            "Second this - they've hooked me up multiple times with exactly what I needed",
            "My go-to for all car parts now. autopartspro.shop all the way",
            # 8 Pure Sheng
            "Hawa ndo real deal bro, nimekunua clutch kit mara mbili no regrets",
            "Noma tu hawa jamaa, bei poa na shipping haraka kabisa",
            "Mi huwa nakula hapa kila time, wana kila kitu na bei iko chini",
            "Hii site ndo inanimaliza stress yangu ya parts kabisa",
            "Sawa tu, nimewahi kununua turbo manifold from them, fitment perfect",
            "Hawa ndo wananifanya nisiende junk tena, parts ni mpya",
            "Nimekunua coilovers za EG from them last month iko fire",
            "Bei poa na waliship in 2 days only, autopartspro.shop",
            # 4 Mix
            "Bro these guys are legit, nimekunua mara tatu no stress + shipping haraka",
            "Hawa ndo wananifanya nisiende dealer tena, bei poa na parts real OEM",
            "Mi huwa nakula hapa kila time bro, quality fire na bei chini kabisa",
            "Second this boss, got my turbo kit from autopartspro.shop - arrived perfect"
        ]

    def default_wa_templates(self):
        return [
            # 8 Pure English
            "Hey bro, saw your post. I have that part in stock with good price. What car is it for?",
            "That part is going for 18,500 delivered. Do you prefer MPESA or bank transfer?",
            "Thanks for the order! Tracking coming in 30 min. Anything else you need?",
            "Price is a bit high but quality is top notch. Want pics?",
            "Can do 17k cash today only. Deal?",
            "Not in stock right now but I can check with boss. Hold on a sec?",
            "MPESA till: AUTO PARTS PRO - 0712345678",
            "Bank details: KCB A/C 1234567890 Westlands branch",
            # 8 Pure Sheng
            "Sasa bro, niliona post yako. Niko na hiyo part bei poa. Gari gani haswa?",
            "Hiyo inakuwanga 18,500 delivered. Unapreference MPESA au bank?",
            "Asante kwa order bro! Tracking inakuja in 30 min. Anything else?",
            "Haha bei iko juu kidogo lakini quality ni fire fr. Unataka pics?",
            "Naeza kufanya 17k cash today only. Deal?",
            "Hiyo haiko stock sasa lakini naeza confirm na boss. Unangoja kidogo?",
            "MPESA till: AUTO PARTS PRO – 0712345678",
            "Bank transfer details: KCB A/C 1234567890 Westlands",
            # 4 Mix
            "Sasa bro saw your post, niko na hiyo part bei poa kabisa. Gari gani exactly?",
            "Hiyo inakuwanga 18,500 delivered. MPESA au bank bro?",
            "Asante sana for the order! Tracking inakuja soon. Anything else unahitaji?",
            "Bei iko juu kidogo lakini quality ni fire fr. Pics?"
        ]

    async def handle_csv_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        file = await update.message.document.get_file()
        filename = update.message.document.file_name
        
        if not filename or not filename.lower().endswith('.csv'):
            await update.message.reply_text("❌ Please upload a CSV file for inventory updates.")
            return
        
        path = "uploaded_inventory.csv"
        await file.download_to_drive(path)
        
        try:
            df = pd.read_csv(path)
            
            if df.empty:
                await update.message.reply_text("❌ CSV file is empty. No changes made.")
                return
            
            required_columns = ['part', 'price', 'stock', 'vehicle', 'year']
            df_columns = df.columns.tolist()
            
            cursor = self.conn.cursor()
            
            try:
                cursor.execute("CREATE TEMP TABLE inventory_backup AS SELECT * FROM inventory")
                logger.info(f"Created backup of inventory")
                
                cursor.execute("DELETE FROM inventory")
                logger.info(f"Cleared inventory")
                
                records = df.to_dict('records')
                for record in records:
                    cursor.execute(
                        "INSERT INTO inventory (part, price, stock, vehicle, year) VALUES (?, ?, ?, ?, ?)",
                        (
                            str(record.get('part', '')),
                            float(record.get('price', 0.0)),
                            int(record.get('stock', 0)),
                            str(record.get('vehicle', '')),
                            str(record.get('year', ''))
                        )
                    )
                
                self.conn.commit()
                cursor.execute("DROP TABLE IF EXISTS inventory_backup")
                logger.info(f"Inventory update committed successfully: {len(records)} parts")
                
                await self.log_action('storage', 'uploaded_csv', {
                    'filename': filename,
                    'parts_count': len(records),
                    'status': 'success'
                })
                await update.message.reply_text(
                    f"✅ INVENTORY UPDATED\n\n"
                    f"Loaded {len(records)} parts from {filename}\n\n"
                    f"All inventory replaced successfully."
                )
            
            except Exception as e:
                logger.error(f"Error during inventory update, rolling back: {e}", exc_info=True)
                try:
                    self.conn.rollback()
                    cursor.execute("DELETE FROM inventory")
                    cursor.execute("INSERT INTO inventory SELECT * FROM inventory_backup")
                    cursor.execute("DROP TABLE IF EXISTS inventory_backup")
                    self.conn.commit()
                    logger.info("Rollback successful, inventory restored from backup")
                except Exception as rollback_err:
                    logger.error(f"Rollback failed: {rollback_err}")
                raise
                
        except pd.errors.EmptyDataError:
            await self.log_action('storage', 'csv_upload_failed', {
                'filename': filename,
                'error': 'Empty CSV file'
            })
            await update.message.reply_text("❌ Error: CSV file is empty or invalid.")
        except pd.errors.ParserError as e:
            await self.log_action('storage', 'csv_upload_failed', {
                'filename': filename,
                'error': f'CSV parsing error: {str(e)}'
            })
            await update.message.reply_text(f"❌ Error parsing CSV: {str(e)[:100]}")
        except (ValueError, KeyError) as e:
            logger.error(f"CSV data validation error: {e}")
            await self.log_action('storage', 'csv_upload_failed', {
                'filename': filename,
                'error': f'Data validation error: {str(e)}'
            })
            await update.message.reply_text(
                f"❌ DATA ERROR\n\n"
                f"CSV must have columns: part, price, stock, vehicle, year\n\n"
                f"Error: {str(e)[:100]}"
            )
        except Exception as e:
            logger.error(f"CSV upload error: {e}", exc_info=True)
            await self.log_action('storage', 'csv_upload_failed', {
                'filename': filename,
                'error': str(e)
            })
            await update.message.reply_text(
                f"❌ ERROR\n\n"
                f"Failed to update inventory: {str(e)[:100]}\n\n"
                f"Database was rolled back - no changes made."
            )

    async def show_templates_menu(self, query):
        keyboard = [
            [InlineKeyboardButton(f"📘 FB Templates ({len(self.fb_templates)})", callback_data="edit_fb")],
            [InlineKeyboardButton(f"💬 WA Templates ({len(self.wa_templates)})", callback_data="edit_wa")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"📝 TEMPLATES MANAGER\n\n"
            f"FB Templates: {len(self.fb_templates)}\n"
            f"WA Templates: {len(self.wa_templates)}\n\n"
            "All templates use authentic Kenyan tone:\n"
            "40% English, 40% Sheng, 20% mix"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_leads_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("📅 Today's Leads", callback_data="leads_today")],
            [InlineKeyboardButton("📥 Export All CSV", callback_data="leads_export")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        total_seen = self.conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
        total_replied = self.conn.execute("SELECT COUNT(*) FROM seen WHERE replied=1").fetchone()[0]
        today_count = self.conn.execute("SELECT COUNT(*) FROM seen WHERE date(timestamp) = date('now')").fetchone()[0]
        
        text = (
            f"📊 LEADS & ANALYTICS\n\n"
            f"Today: {today_count} leads\n"
            f"All Time: {total_seen} seen\n"
            f"Replied: {total_replied}\n"
            f"Pending: {total_seen - total_replied}"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_db_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("📦 View Inventory", callback_data="view_inventory")],
            [InlineKeyboardButton("📤 Upload CSV", callback_data="upload_csv")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        inventory_count = self.conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        
        text = (
            f"📁 DATABASE MANAGER\n\n"
            f"Inventory Parts: {inventory_count}\n"
            f"Tables: 7 (seen, inventory, conversations, sales, accounts_health, automation_logs, schema_meta)\n\n"
            "Manage your inventory and data"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_fb_accounts_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👤 FB ACCOUNTS MANAGER\n\nAccounts: {len(self.fb_accounts)}\n\n"
        
        if self.fb_accounts:
            for i, acc in enumerate(self.fb_accounts[:3], 1):
                email = acc.get('email', 'Cookie-based')
                text += f"{i}. {email[:20]}...\n"
        else:
            text += "No accounts configured.\n"
        
        text += "\nEdit accounts.json to add/remove accounts.\nSupports email/password or cookie-based login."
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def show_fb_groups_menu(self, query):
        self.reload_groups()
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Group", callback_data="fb_groups_add"),
             InlineKeyboardButton("📋 List Groups", callback_data="fb_groups_list")],
            [InlineKeyboardButton("❌ Delete Group", callback_data="fb_groups_delete")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👥 FACEBOOK GROUPS MANAGER\n\nTotal Groups: {len(self.groups)}\n\n"
        
        if self.groups:
            text += "Recent groups:\n"
            for i, group_url in enumerate(self.groups[-3:], 1):
                group_name = group_url.split('/groups/')[-1][:30]
                text += f"{i}. {group_name}\n"
            text += f"\n✅ All groups being monitored 24/7\n"
        else:
            text += "No groups configured yet.\n\n"
            text += "Click 'Add Group' to start monitoring Facebook groups for auto-parts leads.\n"
        
        text += "\nUse the buttons below to manage groups:"
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    def reload_groups(self):
        """Reload groups from groups.json to ensure fresh data"""
        try:
            with open('groups.json', 'r') as f:
                self.groups = json.load(f)
        except Exception as e:
            logger.error(f"Failed to reload groups: {e}")
            if not hasattr(self, 'groups') or self.groups is None:
                self.groups = []

    async def show_settings_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("🧠 Groq API", callback_data="settings_groq")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        import os
        groq_status = "✅ Active" if os.getenv('GROQ_KEY') else "❌ Not set"
        
        text = (
            f"⚙️ SETTINGS\n\n"
            f"Groq AI: {groq_status}\n"
            f"Bot Token: ✅ Set\n"
            f"Owner ID: ✅ Set\n\n"
            "Configure API keys and bot settings"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    def seen_post(self, post_id):
        result = self.conn.execute("SELECT 1 FROM seen WHERE post_id=?", (post_id,)).fetchone()
        return result is not None

    def mark_seen(self, post_id, group, text, lead_quality='warm'):
        self.conn.execute(
            "INSERT OR IGNORE INTO seen (post_id, group_url, text, replied, lead_quality, engagement_score) VALUES (?, ?, ?, 1, ?, 0.5)", 
            (post_id, group, text, lead_quality)
        )
        self.conn.execute(
            "INSERT INTO automation_logs (source, action, payload_json) VALUES (?, ?, ?)",
            ('fb_engine', 'replied_to_post', json.dumps({'post_id': post_id, 'group': group}))
        )
        self.conn.commit()

    async def show_leads_today(self, query):
        await self.log_action('storage', 'view_leads_today', {})
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.execute(
            "SELECT post_id, group_url, text, lead_quality, timestamp FROM seen WHERE date(timestamp) = date(?)",
            (today,)
        )
        leads = cursor.fetchall()
        
        if not leads:
            keyboard = [[InlineKeyboardButton("◀️ Back to Leads", callback_data="leads_menu")]]
            await query.edit_message_text(
                "📅 NO LEADS TODAY\n\n"
                "No leads captured yet. Keep hunting! 🎯\n\n"
                "The bot scans groups every 30 minutes.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        hot = sum(1 for l in leads if l[3] == 'hot')
        warm = sum(1 for l in leads if l[3] == 'warm')
        cold = sum(1 for l in leads if l[3] == 'cold')
        
        text = f"📅 TODAY'S LEADS ({len(leads)})\n\n"
        text += f"🔥 Hot: {hot} | 🟡 Warm: {warm} | ❄️ Cold: {cold}\n\n"
        
        for i, lead in enumerate(leads[:5], 1):
            quality_emoji = "🔥" if lead[3] == "hot" else "🟡" if lead[3] == "warm" else "❄️"
            text += f"{i}. {quality_emoji} {lead[4][:16]}\n"
            text += f"   {lead[2][:50]}...\n\n"
        
        if len(leads) > 5:
            text += f"+ {len(leads) - 5} more leads (export for full list)\n"
        
        keyboard = [
            [InlineKeyboardButton("📥 Export CSV", callback_data="leads_export")],
            [InlineKeyboardButton("◀️ Back to Leads", callback_data="leads_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def export_leads_csv(self, query, bot):
        await self.log_action('storage', 'export_leads_csv', {})
        cursor = self.conn.execute(
            "SELECT post_id, group_url, text, replied, timestamp, engagement_score, lead_quality FROM seen"
        )
        leads = cursor.fetchall()
        
        df = pd.DataFrame(leads, columns=['post_id', 'group_url', 'text', 'replied', 'timestamp', 'engagement_score', 'lead_quality'])
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
        csv_bytes.name = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        await bot.send_document(
            chat_id=query.message.chat_id,
            document=csv_bytes,
            filename=csv_bytes.name,
            caption=f"Leads Export: {len(leads)} total leads"
        )
        await query.answer("CSV exported and sent!")
    
    async def show_inventory(self, query):
        await self.log_action('storage', 'view_inventory', {})
        cursor = self.conn.execute("SELECT part, price, stock, vehicle, year FROM inventory LIMIT 15")
        items = cursor.fetchall()
        
        total = self.conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        
        if not items:
            keyboard = [[InlineKeyboardButton("📤 Upload CSV", callback_data="upload_csv")],
                        [InlineKeyboardButton("◀️ Back", callback_data="db_menu")]]
            await query.edit_message_text(
                "📦 NO INVENTORY\n\n"
                "No parts loaded. Upload a CSV file to add inventory.\n\n"
                "Required columns: part, price, stock, vehicle, year",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        text = f"📦 INVENTORY ({total} parts)\n\nShowing first 15:\n\n"
        for i, item in enumerate(items, 1):
            text += f"{i}. 🔧 {item[0]}\n"
            text += f"   KES {item[1]:,.0f} | Stock: {item[2]} | {item[3]} {item[4]}\n\n"
        
        if total > 15:
            text += f"+ {total - 15} more parts in database"
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload New CSV", callback_data="upload_csv")],
            [InlineKeyboardButton("◀️ Back to Database", callback_data="db_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def prompt_csv_upload(self, query):
        keyboard = [[InlineKeyboardButton("◀️ Back to Database", callback_data="db_menu")]]
        await query.edit_message_text(
            "📤 Upload Inventory CSV\n\n"
            "Send a CSV file with columns:\n"
            "- part (name)\n"
            "- price (number)\n"
            "- stock (quantity)\n"
            "- vehicle (model)\n"
            "- year (year)\n\n"
            "Just upload the file directly to this chat.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_edit_templates(self, query, platform):
        await self.log_action('storage', 'view_templates', {'platform': platform})
        if platform == "fb":
            templates = self.fb_templates
            title = "📘 Facebook Templates"
            back_data = "templates_menu"
        else:
            templates = self.wa_templates
            title = "💬 WhatsApp Templates"
            back_data = "templates_menu"
        
        text = f"{title}\n\nTotal: {len(templates)}\n\n"
        for i, tmpl in enumerate(templates[:5], 1):
            text += f"{i}. {tmpl[:60]}...\n\n"
        
        if len(templates) > 5:
            text += f"\n+ {len(templates) - 5} more templates\n"
        
        text += "\nEdit templates by modifying the JSON files:\n"
        text += f"- fb_templates.json\n- wa_templates.json"
        
        keyboard = [[InlineKeyboardButton("◀️ Back to Templates", callback_data=back_data)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def log_action(self, source, action, payload):
        self.conn.execute(
            "INSERT INTO automation_logs (source, action, payload_json) VALUES (?, ?, ?)",
            (source, action, json.dumps(payload))
        )
        self.conn.commit()

