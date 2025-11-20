# crud_handlers.py - CRUD operations for Groups, Accounts, and WhatsApp Numbers
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

logger = logging.getLogger("CRUD")

WAITING_GROUP_URL, WAITING_ACCOUNT_TYPE, WAITING_ACCOUNT_NAME, WAITING_ACCOUNT_EMAIL, WAITING_ACCOUNT_PASSWORD, WAITING_ACCOUNT_COOKIES, WAITING_WA_SESSION_NAME = range(7)

class CRUDHandlers:
    def __init__(self, storage, wa_engine):
        self.storage = storage
        self.wa_engine = wa_engine
        self.groups_file = "groups.json"
        self.accounts_file = "accounts.json"
        self.wa_numbers_file = "wa_numbers.json"
    
    def load_json(self, filename):
        """Load JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return []
    
    def save_json(self, filename, data):
        """Save JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            return False
    
    async def start_add_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the add group conversation"""
        await update.message.reply_text(
            "📘 ADD FACEBOOK GROUP\n\n"
            "Please send me the Facebook group URL.\n\n"
            "Example: https://www.facebook.com/groups/kenyacarscene\n\n"
            "Send /cancel to cancel."
        )
        return WAITING_GROUP_URL
    
    async def receive_group_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and save the group URL"""
        url = update.message.text.strip()
        
        if not url.startswith('https://www.facebook.com/groups/'):
            await update.message.reply_text(
                "❌ Invalid URL\n\n"
                "Please send a valid Facebook group URL starting with:\n"
                "https://www.facebook.com/groups/\n\n"
                "Try again or send /cancel"
            )
            return WAITING_GROUP_URL
        
        groups = self.load_json(self.groups_file)
        
        if url in groups:
            await update.message.reply_text(
                "⚠️ ALREADY EXISTS\n\n"
                f"This group is already in your list:\n{url}\n\n"
                "Send another URL or /cancel"
            )
            return WAITING_GROUP_URL
        
        groups.append(url)
        
        if self.save_json(self.groups_file, groups):
            self.storage.groups = groups
            self.storage.reload_groups()
            await update.message.reply_text(
                f"✅ GROUP ADDED!\n\n"
                f"URL: {url}\n\n"
                f"Total groups: {len(groups)}\n\n"
                f"The bot will now monitor this group for auto-parts requests."
            )
        else:
            await update.message.reply_text(
                "❌ FAILED TO SAVE\n\n"
                "There was an error saving the group. Please try again."
            )
        
        return ConversationHandler.END
    
    async def list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all Facebook groups"""
        groups = self.load_json(self.groups_file)
        
        if not groups:
            await update.message.reply_text(
                "📘 NO GROUPS CONFIGURED\n\n"
                "Use /add_group to add your first Facebook group."
            )
            return
        
        text = f"📘 FACEBOOK GROUPS ({len(groups)})\n\n"
        for i, url in enumerate(groups, 1):
            text += f"{i}. {url}\n"
        
        text += f"\n✅ Active monitoring\n\nUse /add_group to add more or /delete_group to remove."
        
        await update.message.reply_text(text)
    
    async def start_delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start delete group conversation"""
        groups = self.load_json(self.groups_file)
        
        if not groups:
            await update.message.reply_text(
                "📘 NO GROUPS TO DELETE\n\n"
                "Use /add_group to add Facebook groups first."
            )
            return ConversationHandler.END
        
        text = f"📘 DELETE FACEBOOK GROUP\n\n"
        text += "Current groups:\n\n"
        for i, url in enumerate(groups, 1):
            text += f"{i}. {url}\n"
        
        text += f"\nSend the number (1-{len(groups)}) of the group to delete, or /cancel to cancel."
        
        await update.message.reply_text(text)
        context.user_data['delete_group_list'] = groups
        return WAITING_GROUP_URL
    
    async def delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a group"""
        try:
            index = int(update.message.text.strip()) - 1
            groups = context.user_data.get('delete_group_list', [])
            
            if index < 0 or index >= len(groups):
                await update.message.reply_text(
                    f"❌ Invalid number\n\n"
                    f"Please send a number between 1 and {len(groups)}, or /cancel"
                )
                return WAITING_GROUP_URL
            
            deleted_url = groups[index]
            groups.pop(index)
            
            if self.save_json(self.groups_file, groups):
                self.storage.groups = groups
                self.storage.reload_groups()
                await update.message.reply_text(
                    f"✅ GROUP DELETED!\n\n"
                    f"Removed: {deleted_url}\n\n"
                    f"Remaining groups: {len(groups)}"
                )
            else:
                await update.message.reply_text(
                    "❌ FAILED TO SAVE\n\n"
                    "There was an error saving changes. Please try again."
                )
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid input\n\n"
                "Please send a number, or /cancel to cancel."
            )
            return WAITING_GROUP_URL
    
    async def start_add_fb_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start add Facebook account conversation"""
        keyboard = [
            [InlineKeyboardButton("🍪 Cookie-based (Recommended)", callback_data="acc_type_cookie")],
            [InlineKeyboardButton("📧 Email/Password", callback_data="acc_type_email")],
            [InlineKeyboardButton("❌ Cancel", callback_data="acc_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👤 ADD FACEBOOK ACCOUNT\n\n"
            "Choose authentication method:\n\n"
            "🍪 **Cookie-based** (Recommended)\n"
            "   - More reliable\n"
            "   - Less likely to trigger blocks\n"
            "   - Requires browser extension\n\n"
            "📧 **Email/Password**\n"
            "   - Simple setup\n"
            "   - May require 2FA\n"
            "   - Higher block risk",
            reply_markup=reply_markup
        )
        return WAITING_ACCOUNT_TYPE
    
    async def receive_account_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive account type selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "acc_cancel":
            await query.edit_message_text("❌ Cancelled")
            return ConversationHandler.END
        
        if query.data == "acc_type_cookie":
            context.user_data['account_type'] = 'cookie'
            await query.edit_message_text(
                "👤 ADD FACEBOOK ACCOUNT (Cookie-based)\n\n"
                "Step 1: Enter a name for this account\n"
                "(e.g., 'KaranjaRacer', 'MainAccount')\n\n"
                "Send the name or /cancel to cancel."
            )
            return WAITING_ACCOUNT_NAME
        else:
            context.user_data['account_type'] = 'email'
            await query.edit_message_text(
                "👤 ADD FACEBOOK ACCOUNT (Email/Password)\n\n"
                "Step 1: Enter a name for this account\n"
                "(e.g., 'MutuaDrift', 'BackupAccount')\n\n"
                "Send the name or /cancel to cancel."
            )
            return WAITING_ACCOUNT_NAME
    
    async def receive_account_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive account name"""
        name = update.message.text.strip()
        context.user_data['account_name'] = name
        
        if context.user_data['account_type'] == 'cookie':
            await update.message.reply_text(
                f"👤 Account: {name}\n\n"
                f"Step 2: Paste your Facebook cookies\n\n"
                f"To get cookies:\n"
                f"1. Install 'EditThisCookie' extension\n"
                f"2. Go to facebook.com (logged in)\n"
                f"3. Click extension, Export\n"
                f"4. Paste the JSON here\n\n"
                f"Or send /cancel"
            )
            return WAITING_ACCOUNT_COOKIES
        else:
            await update.message.reply_text(
                f"👤 Account: {name}\n\n"
                f"Step 2: Enter the Facebook email address\n\n"
                f"Send the email or /cancel to cancel."
            )
            return WAITING_ACCOUNT_EMAIL
    
    async def receive_account_cookies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and save cookie-based account"""
        try:
            cookies_text = update.message.text.strip()
            cookies = json.loads(cookies_text)
            
            if not isinstance(cookies, list):
                await update.message.reply_text(
                    "❌ Invalid format\n\n"
                    "Cookies must be a JSON array. Please try again or /cancel"
                )
                return WAITING_ACCOUNT_COOKIES
            
            name = context.user_data['account_name']
            accounts = self.load_json(self.accounts_file)
            
            new_account = {
                "name": name,
                "cookies": cookies
            }
            
            accounts.append(new_account)
            
            if self.save_json(self.accounts_file, accounts):
                self.storage.fb_accounts = accounts
                await update.message.reply_text(
                    f"✅ FACEBOOK ACCOUNT ADDED!\n\n"
                    f"Name: {name}\n"
                    f"Type: Cookie-based\n"
                    f"Cookies: {len(cookies)} entries\n\n"
                    f"Total accounts: {len(accounts)}\n\n"
                    f"The bot will now use this account for Facebook automation."
                )
            else:
                await update.message.reply_text(
                    "❌ FAILED TO SAVE\n\n"
                    "There was an error saving the account. Please try again."
                )
            
            return ConversationHandler.END
            
        except json.JSONDecodeError:
            await update.message.reply_text(
                "❌ Invalid JSON\n\n"
                "Please paste valid JSON from EditThisCookie, or /cancel"
            )
            return WAITING_ACCOUNT_COOKIES
    
    async def receive_account_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive account email"""
        email = update.message.text.strip()
        context.user_data['account_email'] = email
        
        await update.message.reply_text(
            f"👤 Account: {context.user_data['account_name']}\n"
            f"📧 Email: {email}\n\n"
            f"Step 3: Enter the Facebook password\n\n"
            f"⚠️ Your password is stored locally and never shared.\n\n"
            f"Send the password or /cancel to cancel."
        )
        return WAITING_ACCOUNT_PASSWORD
    
    async def receive_account_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and save email/password account"""
        password = update.message.text.strip()
        name = context.user_data['account_name']
        email = context.user_data['account_email']
        
        accounts = self.load_json(self.accounts_file)
        
        new_account = {
            "name": name,
            "email": email,
            "password": password
        }
        
        accounts.append(new_account)
        
        if self.save_json(self.accounts_file, accounts):
            self.storage.fb_accounts = accounts
            
            await update.message.delete()
            
            await update.message.reply_text(
                f"✅ FACEBOOK ACCOUNT ADDED!\n\n"
                f"Name: {name}\n"
                f"Type: Email/Password\n"
                f"Email: {email}\n\n"
                f"Total accounts: {len(accounts)}\n\n"
                f"The bot will now use this account for Facebook automation.\n\n"
                f"🗑️ Your password message was deleted for security."
            )
        else:
            await update.message.reply_text(
                "❌ FAILED TO SAVE\n\n"
                "There was an error saving the account. Please try again."
            )
        
        return ConversationHandler.END
    
    async def list_fb_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all Facebook accounts"""
        accounts = self.load_json(self.accounts_file)
        
        if not accounts:
            await update.message.reply_text(
                "👤 NO ACCOUNTS CONFIGURED\n\n"
                "Use /add_fb_account to add your first Facebook account."
            )
            return
        
        text = f"👤 FACEBOOK ACCOUNTS ({len(accounts)})\n\n"
        for i, acc in enumerate(accounts, 1):
            auth_type = "🍪 Cookie" if 'cookies' in acc else "📧 Email"
            email = acc.get('email', 'N/A')
            cookie_count = f" ({len(acc.get('cookies', []))} cookies)" if 'cookies' in acc else ""
            text += f"{i}. {acc['name']}\n"
            text += f"   Type: {auth_type}{cookie_count}\n"
            if 'email' in acc:
                text += f"   Email: {email}\n"
            text += "\n"
        
        text += f"Use /add_fb_account to add more or /remove_fb_account to remove."
        
        await update.message.reply_text(text)
    
    async def list_fb_accounts_callback(self, query):
        """List all Facebook accounts (callback query version)"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        accounts = self.load_json(self.accounts_file)
        
        if not accounts:
            keyboard = [
                [InlineKeyboardButton("➕ Add Account", callback_data="fb_accounts_add")],
                [InlineKeyboardButton("◀️ Back", callback_data="fb_accounts")]
            ]
            await query.edit_message_text(
                "👤 NO ACCOUNTS CONFIGURED\n\n"
                "Use 'Add Account' below or /add_fb_account command.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        text = f"👤 FACEBOOK ACCOUNTS ({len(accounts)})\n\n"
        for i, acc in enumerate(accounts, 1):
            auth_type = "🍪 Cookie" if 'cookies' in acc else "📧 Email"
            email = acc.get('email', 'N/A')
            cookie_count = f" ({len(acc.get('cookies', []))} cookies)" if 'cookies' in acc else ""
            text += f"{i}. {acc['name']}\n"
            text += f"   Type: {auth_type}{cookie_count}\n"
            if 'email' in acc:
                text += f"   Email: {email}\n"
            text += "\n"
        
        text += f"\n✅ All {len(accounts)} accounts configured"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="fb_accounts")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def start_add_wa_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start add WhatsApp number conversation"""
        await update.message.reply_text(
            "📱 ADD WHATSAPP NUMBER\n\n"
            "Enter a name for this WhatsApp session.\n"
            "(e.g., 'main-number', 'sales-line', 'support')\n\n"
            "Send the name or /cancel to cancel."
        )
        return WAITING_WA_SESSION_NAME
    
    async def receive_wa_session_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive session name and trigger QR code generation"""
        session_name = update.message.text.strip().replace(' ', '-').lower()
        
        await update.message.reply_text(
            f"📱 Creating WhatsApp session: {session_name}\n\n"
            f"Generating QR code... please wait ⏳"
        )
        
        success = await self.wa_engine.add_whatsapp_number(
            session_name,
            update.callback_query if hasattr(update, 'callback_query') else None,
            context.bot
        )
        
        if success:
            wa_numbers = self.load_json(self.wa_numbers_file)
            wa_numbers.append({
                "number": session_name,
                "name": session_name,
                "active": True
            })
            self.save_json(self.wa_numbers_file, wa_numbers)
            self.storage.wa_numbers = wa_numbers
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel any conversation"""
        await update.message.reply_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to return to the main menu."
        )
        return ConversationHandler.END
    
    def get_conversation_handlers(self):
        """Get all conversation handlers"""
        return [
            ConversationHandler(
                entry_points=[CommandHandler('add_group', self.start_add_group)],
                states={
                    WAITING_GROUP_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_group_url)]
                },
                fallbacks=[CommandHandler('cancel', self.cancel)]
            ),
            ConversationHandler(
                entry_points=[CommandHandler('delete_group', self.start_delete_group)],
                states={
                    WAITING_GROUP_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.delete_group)]
                },
                fallbacks=[CommandHandler('cancel', self.cancel)]
            ),
            ConversationHandler(
                entry_points=[CommandHandler('add_fb_account', self.start_add_fb_account)],
                states={
                    WAITING_ACCOUNT_TYPE: [CallbackQueryHandler(self.receive_account_type)],
                    WAITING_ACCOUNT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_account_name)],
                    WAITING_ACCOUNT_COOKIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_account_cookies)],
                    WAITING_ACCOUNT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_account_email)],
                    WAITING_ACCOUNT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_account_password)]
                },
                fallbacks=[CommandHandler('cancel', self.cancel)]
            ),
            ConversationHandler(
                entry_points=[CommandHandler('add_wa_number', self.start_add_wa_number)],
                states={
                    WAITING_WA_SESSION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_wa_session_name)]
                },
                fallbacks=[CommandHandler('cancel', self.cancel)]
            )
        ]
    
    def get_command_handlers(self):
        """Get simple command handlers"""
        return [
            CommandHandler('list_groups', self.list_groups),
            CommandHandler('list_fb_accounts', self.list_fb_accounts)
        ]
