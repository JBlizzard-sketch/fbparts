# wa_engine.py - WhatsApp Engine for EMPIRE v13 with Baileys Integration
import asyncio
import logging
import subprocess
import httpx
import json
import os
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

logger = logging.getLogger("WAEngine")

class WAEngine:
    def __init__(self, brain, storage):
        self.brain = brain
        self.storage = storage
        self.active = False
        self.baileys_process = None
        self.baileys_url = "http://localhost:3000"
        self.sessions = {}
        self.message_poll_task = None
        self.qr_callbacks = {}
        
    async def start_baileys_server(self):
        """Start the Baileys WhatsApp server with async subprocess management"""
        if self.baileys_process is not None:
            try:
                returncode = self.baileys_process.returncode
                if returncode is None:
                    logger.info("Baileys server already running")
                    return True
            except:
                pass
            
        try:
            logger.info("Starting Baileys WhatsApp server...")
            self.baileys_process = await asyncio.create_subprocess_exec(
                'node', 'baileys_client.js', 'server', '3000',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True
            )
            
            asyncio.create_task(self._drain_baileys_output())
            
            await asyncio.sleep(5)
            
            if self.baileys_process.returncode is None:
                logger.info("✅ Baileys server started successfully on port 3000")
                return True
            else:
                exit_code = self.baileys_process.returncode
                logger.error(f"❌ Baileys server terminated with exit code {exit_code}")
                self.baileys_process = None
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Baileys server: {e}", exc_info=True)
            if self.baileys_process:
                try:
                    self.baileys_process.terminate()
                    await self.baileys_process.wait()
                except:
                    pass
            self.baileys_process = None
            return False
    
    async def _drain_baileys_output(self):
        """Continuously drain Baileys stdout/stderr to prevent pipe buffer from filling"""
        if not self.baileys_process:
            return
        
        try:
            async def read_stream(stream, stream_name):
                try:
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            logger.debug(f"Baileys {stream_name}: {decoded_line}")
                except Exception as e:
                    logger.error(f"Error reading {stream_name}: {e}")
            
            await asyncio.gather(
                read_stream(self.baileys_process.stdout, "STDOUT"),
                read_stream(self.baileys_process.stderr, "STDERR"),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error draining Baileys output: {e}")
    
    async def stop_baileys_server(self):
        """Stop the Baileys WhatsApp server with async-safe process termination"""
        if self.baileys_process:
            try:
                self.baileys_process.terminate()
                try:
                    await asyncio.wait_for(self.baileys_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Baileys server did not terminate gracefully, killing...")
                    self.baileys_process.kill()
                    await self.baileys_process.wait()
            except Exception as e:
                logger.error(f"Error stopping Baileys server: {e}")
            finally:
                self.baileys_process = None
                logger.info("Baileys server stopped")
    
    async def get_status(self):
        """Get status of all WhatsApp sessions"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.baileys_url}/status", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get Baileys status: {e}")
        return {"clients": [], "messagesInQueue": 0}
    
    async def add_whatsapp_number(self, session_name, query=None, bot=None):
        """Add a new WhatsApp number and generate QR code with proper process management"""
        process = None
        drain_tasks = []
        try:
            logger.info(f"Adding WhatsApp session: {session_name}")
            
            process = await asyncio.create_subprocess_exec(
                'node', 'baileys_client.js', 'add', session_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            async def drain_stdout():
                """Drain stdout to prevent buffer blocking"""
                try:
                    while True:
                        line = await process.stdout.readline()
                        if not line:
                            break
                        logger.debug(f"QR stdout: {line.decode().strip()}")
                except Exception as e:
                    logger.error(f"Error draining QR stdout: {e}")
            
            async def drain_stderr():
                """Drain stderr to prevent buffer blocking"""
                try:
                    while True:
                        line = await process.stderr.readline()
                        if not line:
                            break
                        logger.warning(f"QR stderr: {line.decode().strip()}")
                except Exception as e:
                    logger.error(f"Error draining QR stderr: {e}")
            
            drain_tasks = [
                asyncio.create_task(drain_stdout()),
                asyncio.create_task(drain_stderr())
            ]
            
            if query and bot:
                await query.edit_message_text(
                    f"📱 ADDING WHATSAPP NUMBER\n\n"
                    f"Session: {session_name}\n\n"
                    f"Waiting for QR code...\n"
                    f"Please wait while we connect..."
                )
            
            await asyncio.sleep(5)
            
            qr_png_path = Path(f'sessions/whatsapp/{session_name}_qr.png')
            event_file = Path(f'sessions/whatsapp/{session_name}_events.json')
            
            max_wait = 60
            waited = 0
            while waited < max_wait:
                if process.returncode is not None:
                    logger.warning(f"QR process exited with code {process.returncode}")
                    break
                
                if qr_png_path.exists():
                    logger.info(f"QR code found for {session_name}")
                    
                    if query and bot:
                        try:
                            with open(qr_png_path, 'rb') as qr_file:
                                await bot.send_photo(
                                    chat_id=query.message.chat_id,
                                    photo=qr_file,
                                    caption=(
                                        f"📱 SCAN THIS QR CODE\n\n"
                                        f"Session: {session_name}\n\n"
                                        f"1. Open WhatsApp on your phone\n"
                                        f"2. Go to Settings > Linked Devices\n"
                                        f"3. Tap 'Link a Device'\n"
                                        f"4. Scan this QR code\n\n"
                                        f"⏱️ QR code expires in 60 seconds"
                                    )
                                )
                            
                            await query.edit_message_text(
                                f"✅ QR CODE SENT!\n\n"
                                f"Check the photo above and scan it with WhatsApp.\n"
                                f"I'll notify you when connected."
                            )
                        except Exception as e:
                            logger.error(f"Failed to send QR code: {e}")
                    
                    break
                
                if event_file.exists():
                    try:
                        with open(event_file, 'r') as f:
                            events = json.load(f)
                            for event in events:
                                if event['event'] == 'connected':
                                    logger.info(f"Session {session_name} connected!")
                                    if query and bot:
                                        await bot.send_message(
                                            chat_id=query.message.chat_id,
                                            text=f"✅ WHATSAPP CONNECTED!\n\n"
                                                 f"Session {session_name} is now active and ready to receive messages."
                                        )
                                    return True
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in event file: {e}")
                
                await asyncio.sleep(2)
                waited += 2
            
            if waited >= max_wait and not qr_png_path.exists():
                if query:
                    await query.edit_message_text(
                        f"⏱️ TIMEOUT\n\n"
                        f"QR code not generated within {max_wait} seconds.\n"
                        f"Please check the logs and try again."
                    )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add WhatsApp number: {e}", exc_info=True)
            if query:
                try:
                    await query.edit_message_text(
                        f"❌ ERROR\n\n"
                        f"Failed to add WhatsApp number: {str(e)[:100]}"
                    )
                except:
                    pass
            return False
        finally:
            for task in drain_tasks:
                if not task.done():
                    task.cancel()
            
            if drain_tasks:
                await asyncio.gather(*drain_tasks, return_exceptions=True)
            
            if process and process.returncode is None:
                try:
                    logger.info(f"Terminating QR code generation process for {session_name}")
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning("QR process did not terminate, killing...")
                        process.kill()
                        await process.wait()
                except Exception as e:
                    logger.error(f"Error terminating QR process: {e}")
    
    async def send_message(self, session_name, jid, message):
        """Send a WhatsApp message via Baileys"""
        try:
            logger.info(f"Sending message to {jid} via {session_name}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.baileys_url}/send",
                    json={
                        "sessionName": session_name,
                        "jid": jid,
                        "message": message
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"✅ Message sent successfully to {jid}")
                        return True
                    else:
                        logger.error(f"❌ Failed to send message: {result.get('error')}")
                        return False
                else:
                    logger.error(f"❌ HTTP {response.status_code}: Failed to send message")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    async def poll_messages(self, bot, owner_id):
        """Poll for new WhatsApp messages and process them"""
        while self.active:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.baileys_url}/messages?limit=10", timeout=5.0)
                    
                    if response.status_code == 200:
                        messages = response.json()
                        
                        for msg in messages:
                            await self.process_message(msg, bot, owner_id)
                
            except Exception as e:
                logger.error(f"Error polling messages: {e}")
            
            await asyncio.sleep(5)
    
    async def process_message(self, msg, bot, owner_id):
        """Process an incoming WhatsApp message"""
        try:
            sender = msg.get('from', 'Unknown')
            message_text = msg.get('message', '')
            session_name = msg.get('sessionName', 'default')
            
            logger.info(f"Processing WhatsApp message from {sender}: {message_text}")
            
            await self.storage.log_action('wa_engine', 'message_received', {
                'from': sender,
                'session': session_name,
                'message': message_text[:100]
            })
            
            reply = await self.brain.generate_response(
                message_text,
                context={
                    'platform': 'whatsapp',
                    'sender': sender,
                    'session': session_name
                }
            )
            
            logger.info(f"Generated reply for WhatsApp: {reply[:50]}...")
            
            sent = await self.send_message(session_name, sender, reply)
            
            await self.storage.log_action('wa_engine', 'auto_reply', {
                'to': sender,
                'reply': reply[:100],
                'sent': sent
            })
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def show_menu(self, query):
        """Show WhatsApp manager menu"""
        status_data = await self.get_status()
        num_clients = len(status_data.get('clients', []))
        messages_in_queue = status_data.get('messagesInQueue', 0)
        
        toggle_text = "⏸️ Stop Service" if self.active else "▶️ Start Service"
        keyboard = [
            [InlineKeyboardButton(f"📱 View Numbers ({len(self.storage.wa_numbers)})", callback_data="wa_list")],
            [InlineKeyboardButton("➕ Add WhatsApp Number", callback_data="wa_add_wizard")],
            [InlineKeyboardButton(toggle_text, callback_data="wa_toggle")],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="wa_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        status_emoji = "🟢 ACTIVE" if self.active else "⚪ PAUSED"
        baileys_status = "🟢 RUNNING" if self.baileys_process and self.baileys_process.returncode is None else "⚪ STOPPED"
        
        text = (
            f"💬 WHATSAPP MANAGER\n\n"
            f"Service Status: {status_emoji}\n"
            f"Baileys Server: {baileys_status}\n"
            f"Connected Sessions: {num_clients}\n"
            f"Numbers Configured: {len(self.storage.wa_numbers)}\n"
            f"Messages in Queue: {messages_in_queue}\n\n"
            f"✨ Full Baileys integration active!\n"
            f"Ready to scan QR codes and receive messages."
        )
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def toggle(self):
        """Toggle WhatsApp service on/off"""
        self.active = not self.active
        status = "started" if self.active else "stopped"
        logger.info(f"WhatsApp service {status}")
        
        if self.active:
            await self.start_baileys_server()
        else:
            if self.message_poll_task:
                self.message_poll_task.cancel()
                self.message_poll_task = None
        
        await self.storage.log_action('wa_engine', 'toggle_service', {'active': self.active})
        return status
    
    async def list_numbers(self, query):
        """List all configured WhatsApp numbers"""
        status_data = await self.get_status()
        connected_sessions = {client['name']: client['status'] for client in status_data.get('clients', [])}
        
        if not self.storage.wa_numbers and not connected_sessions:
            keyboard = [
                [InlineKeyboardButton("➕ Add WhatsApp Number", callback_data="wa_add_wizard")],
                [InlineKeyboardButton("◀️ Back", callback_data="wa_menu")]
            ]
            await query.edit_message_text(
                "📱 NO NUMBERS CONFIGURED\n\n"
                "Click 'Add WhatsApp Number' to connect your first WhatsApp account.\n\n"
                "You can connect multiple WhatsApp numbers for better coverage.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        text = f"📱 WHATSAPP SESSIONS\n\n"
        
        for session_name, status in connected_sessions.items():
            is_connected = status.get('isConnected', False)
            status_emoji = "🟢" if is_connected else "🔴"
            has_qr = status.get('hasQR', False)
            qr_status = " (QR pending)" if has_qr else ""
            text += f"{status_emoji} {session_name}{qr_status}\n"
            if is_connected:
                text += f"   Status: Connected ✅\n"
            else:
                text += f"   Status: Disconnected\n"
            text += "\n"
        
        if not connected_sessions:
            text += "No active sessions.\n\n"
        
        text += f"\nConfigured in wa_numbers.json: {len(self.storage.wa_numbers)}"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Number", callback_data="wa_add_wizard")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="wa_list")],
            [InlineKeyboardButton("◀️ Back to WhatsApp", callback_data="wa_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def start_all(self, bot, owner_id):
        """Start all WhatsApp services with bot context"""
        self.active = True
        self.bot = bot
        self.owner_id = owner_id
        logger.info("Starting WhatsApp service with Baileys integration...")
        
        if await self.start_baileys_server():
            logger.info("✅ WhatsApp service started successfully")
            self.message_poll_task = asyncio.create_task(
                self.poll_messages(bot, owner_id)
            )
        else:
            logger.error("❌ Failed to start Baileys server")
            self.active = False
        
        while self.active:
            await asyncio.sleep(60)
