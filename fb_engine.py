# fb_engine.py
from playwright.async_api import async_playwright
import random
import asyncio
import logging
import hashlib
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger("FBEngine")

class FBEngine:
    def __init__(self, brain, storage):
        self.brain = brain
        self.storage = storage
        self.active = False
        self.hist_progress = {"running": False, "current_group": None, "posts_scraped": 0}

    async def show_menu(self, query):
        toggle_text = "⏸️ Stop Scan" if self.active else "▶️ Start Scan"
        keyboard = [
            [InlineKeyboardButton(toggle_text, callback_data="fb_toggle")],
            [InlineKeyboardButton("⚡ Force Scan Now", callback_data="fb_force")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        status = "🟢 ACTIVE" if self.active else "⚪ PAUSED"
        
        text = (
            f"📘 LIVE FB BOT\n\n"
            f"Status: {status}\n"
            f"Accounts: {len(self.storage.fb_accounts)}\n"
            f"Groups: {len(self.storage.groups)}\n"
            f"Scan Interval: 30 min\n\n"
            "Automatically monitors FB groups for auto-part requests"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_historical_menu(self, query):
        start_text = "⏸️ Stop Scrape" if self.hist_progress["running"] else "▶️ Start Scrape"
        keyboard = [
            [InlineKeyboardButton(start_text, callback_data="hist_start")],
            [InlineKeyboardButton("📊 View Progress", callback_data="hist_progress")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        status = "🟢 RUNNING" if self.hist_progress["running"] else "⚪ IDLE"
        
        text = (
            f"⏳ HISTORICAL SCRAPER\n\n"
            f"Status: {status}\n"
            f"Posts Scraped: {self.hist_progress['posts_scraped']}\n\n"
            "One-time scrape of last 3 months of posts\n"
            "from all configured Facebook groups"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def toggle(self):
        self.active = not self.active
        status = "started" if self.active else "stopped"
        logger.info(f"FB live scanning {status}")
        await self.storage.log_action('fb_engine', 'toggle_scan', {'active': self.active})
        return status
    
    async def force_scan(self):
        logger.info("Force scanning Facebook groups")
        await self.storage.log_action('fb_engine', 'force_scan', {})
        
        # Force scan bypasses active flag
        temp_active = self.active
        self.active = True
        try:
            await self.live_cycle()
        finally:
            self.active = temp_active
        
        return "Force scan completed"
    
    async def start_historical_scrape(self):
        if self.hist_progress["running"]:
            return "Historical scrape already running"
        
        self.hist_progress = {"running": True, "current_group": None, "posts_scraped": 0}
        await self.storage.log_action('fb_engine', 'start_historical_scrape', {})
        asyncio.create_task(self._historical_scrape_worker())
        return "Historical scrape started"
    
    async def _historical_scrape_worker(self):
        try:
            async with async_playwright() as p:
                for group in self.storage.groups:
                    self.hist_progress["current_group"] = group
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=f"sessions/historical",
                        headless=True,
                        viewport={"width": 1920, "height": 1080}
                    )
                    page = context.pages[0] if context.pages else await context.new_page()
                    await page.goto(group)
                    
                    for _ in range(20):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                    
                    posts = await page.query_selector_all("article")
                    for post in posts:
                        text_elem = await post.query_selector("div[dir='auto']")
                        if not text_elem:
                            continue
                        text = await text_elem.inner_text()
                        post_id = hashlib.sha256(f"{group}:{text}".encode('utf-8')).hexdigest()[:32]
                        
                        if not self.storage.seen_post(post_id):
                            if any(kw in text.lower() for kw in ["wtb", "need", "looking for", "iso", "part out"]):
                                self.storage.mark_seen(post_id, group, text, lead_quality='cold')
                                self.hist_progress["posts_scraped"] += 1
                    
                    await context.close()
        except Exception as e:
            logger.error(f"Historical scrape error: {e}")
        finally:
            self.hist_progress["running"] = False
    
    async def live_cycle(self):
        if not self.active:
            return
        
        async with async_playwright() as p:
            for acc in self.storage.fb_accounts:
                if not self.active:
                    break
                    
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=f"sessions/{acc.get('name', 'default')}",
                    headless=True,
                    viewport={"width": 1920, "height": 1080}
                )
                if "cookies" in acc:
                    await context.add_cookies(acc["cookies"])
                page = context.pages[0] if context.pages else await context.new_page()
                
                for group in self.storage.groups:
                    if not self.active:
                        break
                        
                    await page.goto(group)
                    await page.wait_for_timeout(5000)
                    posts = await page.query_selector_all("article")
                    
                    for post in posts:
                        if not self.active:
                            break
                            
                        text_elem = await post.query_selector("div[dir='auto']")
                        if not text_elem:
                            continue
                        text = await text_elem.inner_text()
                        
                        fb_post_id = await post.get_attribute("data-ft")
                        if fb_post_id:
                            post_id = fb_post_id
                        else:
                            post_id = hashlib.sha256(f"{group}:{text}".encode('utf-8')).hexdigest()[:32]
                        
                        if self.storage.seen_post(post_id):
                            continue
                        if any(kw in text.lower() for kw in ["wtb", "need", "looking for", "iso", "part out"]):
                            try:
                                reply = await self.brain.fb_reply(text)
                                reply_box = await post.query_selector("textarea")
                                if reply_box:
                                    await reply_box.fill(reply)
                                    await reply_box.press("Enter")
                                    self.storage.mark_seen(post_id, group, text, lead_quality='hot')
                                    logger.info(f"Replied to post in {group}")
                                    await asyncio.sleep(random.uniform(8, 20))
                                else:
                                    logger.warning(f"Could not find reply box for post in {group}")
                                    self.storage.mark_seen(post_id, group, text, lead_quality='warm')
                            except Exception as e:
                                logger.error(f"Error replying to post: {e}")
                                self.storage.mark_seen(post_id, group, text, lead_quality='warm')
                
                await context.close()
                await asyncio.sleep(random.uniform(60, 120))
