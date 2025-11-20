# main.py - EMPIRE v13 EXPANDED - NOV 20 2025
import asyncio
import json
import logging
import os
import random
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

from brain import GroqBrain
from storage import Storage
from fb_engine import FBEngine
from wa_engine import WAEngine
from crud_handlers import CRUDHandlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("EMPIRE")

TOKEN = os.getenv("BOT_TOKEN")
owner_id_raw = os.getenv("OWNER_ID", "0")
OWNER_ID = int(owner_id_raw.replace("Id:", "").strip())

if not TOKEN or not OWNER_ID:
    raise ValueError("Set BOT_TOKEN and OWNER_ID in .env")

storage = Storage()
brain = GroqBrain(os.getenv("GROQ_KEY", ""), storage)
fb = FBEngine(brain, storage)
wa = WAEngine(brain, storage)
crud = CRUDHandlers(storage, wa)

app = Application.builder().token(TOKEN).build()

PERSISTENT_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🏠 Home"), KeyboardButton("📊 Leads"), KeyboardButton("⚙️ Operations")],
    [KeyboardButton("📁 Database"), KeyboardButton("🔧 Settings")]
], resize_keyboard=True)

def get_main_stats_text():
    parts_count = storage.conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]
    leads_today_count = storage.conn.execute("SELECT COUNT(*) FROM seen WHERE date(timestamp) = date('now')").fetchone()[0] or 0
    return (
        "🚀 EMPIRE v13 — HUNTING & CLOSING\n\n"
        f"🧠 Groq Brain: {'ON 🔥' if brain.online else 'Fallback'}\n"
        f"📘 FB Accounts: {len(storage.fb_accounts)}\n"
        f"👥 Groups: {len(storage.groups)}\n"
        f"📱 WA Numbers: {len(storage.wa_numbers)}\n"
        f"🔧 Parts: {parts_count}\n"
        f"📈 Leads Today: {leads_today_count}\n\n"
        "Choose a module:"
    )

async def render_main_menu(message_or_query, edit=False):
    keyboard = [
        [InlineKeyboardButton("📘 Live FB Bot", callback_data="fb_menu"), 
         InlineKeyboardButton("💬 WhatsApp", callback_data="wa_menu")],
        [InlineKeyboardButton("👥 FB Groups", callback_data="fb_groups_menu"),
         InlineKeyboardButton("👤 FB Accounts", callback_data="fb_accounts")],
        [InlineKeyboardButton("📝 Templates", callback_data="templates_menu"), 
         InlineKeyboardButton("📊 Leads", callback_data="leads_menu")],
        [InlineKeyboardButton("⏳ Historical Scan", callback_data="hist_menu"), 
         InlineKeyboardButton("📁 Database", callback_data="db_menu")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = get_main_stats_text()
    
    if edit:
        await message_or_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message_or_query.reply_text(text, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to EMPIRE v13!\n\nUse the persistent menu below or the inline buttons.",
        reply_markup=PERSISTENT_MENU
    )
    await render_main_menu(update.message)

async def handle_persistent_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🏠 Home":
        await render_main_menu(update.message)
    elif text == "📊 Leads":
        keyboard = [
            [InlineKeyboardButton("📅 Today's Leads", callback_data="leads_today")],
            [InlineKeyboardButton("📥 Export CSV", callback_data="leads_export")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        stats = storage.conn.execute(
            "SELECT COUNT(*), COUNT(CASE WHEN replied=1 THEN 1 END) FROM seen WHERE date(timestamp) = date('now')"
        ).fetchone()
        text = (
            f"📊 LEADS DASHBOARD\n\n"
            f"Today: {stats[0]} leads\n"
            f"Replied: {stats[1]}\n"
            f"Pending: {stats[0] - stats[1]}\n\n"
            "What would you like to do?"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "⚙️ Operations":
        keyboard = [
            [InlineKeyboardButton("📘 Facebook Bot", callback_data="fb_menu")],
            [InlineKeyboardButton("💬 WhatsApp", callback_data="wa_menu")],
            [InlineKeyboardButton("⏳ Historical Scan", callback_data="hist_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        text = (
            f"⚙️ OPERATIONS CENTER\n\n"
            f"FB Scanning: {'ACTIVE' if fb.active else 'PAUSED'}\n"
            f"WA Service: {'ACTIVE' if wa.active else 'PAUSED'}\n"
            f"Historical Scan: {'RUNNING' if fb.hist_progress['running'] else 'IDLE'}\n\n"
            "Choose an operation:"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "📁 Database":
        keyboard = [
            [InlineKeyboardButton("📦 View Inventory", callback_data="view_inventory")],
            [InlineKeyboardButton("📤 Upload CSV", callback_data="upload_csv")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        total_parts = storage.conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        text = f"📁 DATABASE MANAGER\n\nInventory Parts: {total_parts}\n\nWhat would you like to do?"
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "🔧 Settings":
        keyboard = [
            [InlineKeyboardButton("🧠 Groq API", callback_data="settings_groq")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        text = (
            f"🔧 SETTINGS\n\n"
            f"Groq Brain: {'ON 🔥' if brain.online else 'OFF (using templates)'}\n\n"
            "Configure bot settings:"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    try:
        await storage.log_action('navigation', 'button_click', {'callback_data': data})
        
        if data == "main_menu":
            await render_main_menu(query, edit=True)
        elif data == "fb_menu":
            await fb.show_menu(query)
        elif data == "wa_menu":
            await wa.show_menu(query)
        elif data == "fb_groups_menu":
            await storage.show_fb_groups_menu(query)
        elif data == "fb_groups_add":
            await query.edit_message_text(
                "👥 ADD FACEBOOK GROUP\n\n"
                "To add a Facebook group, use the command:\n"
                "/add_group\n\n"
                "Then send the Facebook group URL.\n"
                "Example: https://www.facebook.com/groups/kenyacarscene",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="fb_groups_menu")]])
            )
        elif data == "fb_groups_list":
            storage.reload_groups()
            if not storage.groups:
                await query.edit_message_text(
                    "📋 NO GROUPS\n\n"
                    "No Facebook groups configured.\n\n"
                    "Use /add_group to add your first group.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="fb_groups_menu")]])
                )
            else:
                text = f"📋 FACEBOOK GROUPS ({len(storage.groups)})\n\n"
                for i, group_url in enumerate(storage.groups, 1):
                    group_name = group_url.split('/groups/')[-1][:40]
                    text += f"{i}. {group_name}\n"
                text += f"\n✅ All {len(storage.groups)} groups actively monitored\n"
                text += "\nUse /delete_group to remove a group."
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="fb_groups_menu")]])
                )
        elif data == "fb_groups_delete":
            await query.edit_message_text(
                "❌ DELETE FACEBOOK GROUP\n\n"
                "To delete a Facebook group, use the command:\n"
                "/delete_group\n\n"
                "You'll be shown a list of groups to choose from.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="fb_groups_menu")]])
            )
        elif data == "templates_menu":
            await storage.show_templates_menu(query)
        elif data == "leads_menu":
            await storage.show_leads_menu(query)
        elif data == "hist_menu":
            await fb.show_historical_menu(query)
        elif data == "db_menu":
            await storage.show_db_menu(query)
        elif data == "fb_accounts":
            await storage.show_fb_accounts_menu(query)
        elif data == "settings_menu":
            await storage.show_settings_menu(query)
        elif data == "fb_toggle":
            status = await fb.toggle()
            await query.answer(f"FB scanning {status}!")
            await fb.show_menu(query)
        elif data == "fb_force":
            await query.answer("Force scan started in background...")
            asyncio.create_task(fb.force_scan())
            await fb.show_menu(query)
        elif data == "wa_toggle":
            status = await wa.toggle()
            await query.answer(f"WhatsApp service {status}!")
            await wa.show_menu(query)
        elif data == "wa_list":
            await wa.list_numbers(query)
        elif data == "leads_today":
            await storage.show_leads_today(query)
        elif data == "leads_export":
            await storage.export_leads_csv(query, app.bot)
        elif data == "hist_start":
            msg = await fb.start_historical_scrape()
            await query.answer(msg)
            await fb.show_historical_menu(query)
        elif data == "hist_progress":
            prog = fb.hist_progress
            if prog["running"]:
                text = (
                    f"⏳ Historical Scrape Progress\n\n"
                    f"Status: RUNNING\n"
                    f"Current Group: {prog['current_group'] or 'N/A'}\n"
                    f"Posts Scraped: {prog['posts_scraped']}"
                )
            else:
                text = (
                    f"⏳ Historical Scrape Progress\n\n"
                    f"Status: IDLE\n"
                    f"Total Posts Scraped: {prog['posts_scraped']}"
                )
            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="hist_progress")], 
                        [InlineKeyboardButton("◀️ Back", callback_data="hist_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif data == "upload_csv":
            await storage.prompt_csv_upload(query)
        elif data == "view_inventory":
            await storage.show_inventory(query)
        elif data == "edit_fb":
            await storage.show_edit_templates(query, "fb")
        elif data == "edit_wa":
            await storage.show_edit_templates(query, "wa")
        elif data == "settings_groq":
            text = (
                f"🧠 Groq API Configuration\n\n"
                f"Status: {'ACTIVE' if brain.online else 'INACTIVE'}\n"
                f"Model: llama-3.1-70b-versatile\n\n"
                f"The Groq API key is set via environment variables.\n"
                f"Current key: {'✅ Set' if os.getenv('GROQ_KEY') else '❌ Not set'}"
            )
            keyboard = [[InlineKeyboardButton("◀️ Back to Settings", callback_data="settings_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif data == "wa_add_wizard":
            keyboard = [[InlineKeyboardButton("◀️ Cancel", callback_data="wa_menu")]]
            await query.edit_message_text(
                "📱 ADD WHATSAPP NUMBER\n\n"
                "To add a WhatsApp number, use the command:\n"
                "/add_wa_number\n\n"
                "This will start a wizard that generates a QR code\n"
                "for you to scan with WhatsApp.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif data == "fb_accounts_add":
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="fb_accounts")]]
            await query.edit_message_text(
                "👤 ADD FACEBOOK ACCOUNT\n\n"
                "To add a Facebook account, use the command:\n"
                "/add_fb_account\n\n"
                "You can add accounts using cookies or email/password.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif data == "fb_accounts_list":
            await crud.list_fb_accounts_callback(query)
        else:
            await query.answer(f"Handler for '{data}' coming soon!")
            logger.warning(f"Unhandled callback: {data}")
            
    except Exception as e:
        logger.error(f"Button handler error for '{data}': {e}", exc_info=True)
        try:
            await query.edit_message_text(
                f"❌ ERROR\n\nSomething went wrong processing this action.\n\n"
                f"Error: {str(e)[:100]}\n\n"
                "Please try again or return to main menu.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
            )
        except:
            pass

app.add_handler(CommandHandler("start", start))

for handler in crud.get_conversation_handlers():
    app.add_handler(handler)

for handler in crud.get_command_handlers():
    app.add_handler(handler)

app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.Document.ALL, storage.handle_csv_upload))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_persistent_menu))

async def empire_loop():
    while True:
        try:
            if fb.active:
                await fb.live_cycle()
        except Exception as e:
            logger.error(f"FB cycle error: {e}")
        await asyncio.sleep(1800)

async def main():
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    logger.info("EMPIRE v13 — EXPANDED BUILD — ONLINE")
    await app.bot.send_message(OWNER_ID, "🚀 EMPIRE v13 — ONLINE\n\nPhases 1.3-1.4 complete!\n\n✅ Persistent sidebar menu\n✅ All buttons wired\n✅ Complete audit logging")

    asyncio.create_task(empire_loop())
    asyncio.create_task(wa.start_all(app.bot, OWNER_ID))

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
