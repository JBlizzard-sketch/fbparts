# brain.py
import os
import httpx
import random
import logging

logger = logging.getLogger("GroqBrain")

class GroqBrain:
    def __init__(self, key="", storage=None):
        self.key = key or os.getenv("GROQ_KEY")
        self.online = bool(self.key)
        self.storage = storage
        self.shop_url = os.getenv("SHOP_URL", "autopartspro.shop")
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER", "254700123456")
        self.model = "llama-3.1-70b-versatile"

    async def ask(self, prompt):
        if not self.online:
            logger.warning("Groq AI offline, using fallback templates")
            if self.storage and hasattr(self.storage, 'fb_templates') and hasattr(self.storage, 'wa_templates'):
                all_templates = self.storage.fb_templates + self.storage.wa_templates
                if all_templates:
                    return random.choice(all_templates)
            return f"Check out {self.shop_url} for quality parts!"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.9
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException as e:
            logger.error(f"Groq API timeout: {e}")
            self.online = False
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API HTTP error {e.response.status_code}: {e}")
            self.online = False
        except (KeyError, IndexError) as e:
            logger.error(f"Groq API response parsing error: {e}")
            self.online = False
        except Exception as e:
            logger.error(f"Unexpected Groq API error: {e}", exc_info=True)
            self.online = False
        
        if self.storage and hasattr(self.storage, 'fb_templates'):
            if self.storage.fb_templates:
                return random.choice(self.storage.fb_templates)
        return f"Check out {self.shop_url} for quality parts!"

    async def fb_reply(self, post_text):
        prompt = f"""You are a Kenyan car owner replying in a Facebook group. Never sound like staff.
Use 40% English, 40% Sheng, 20% mix. Include both links at the end.
Post: {post_text}
Reply:"""
        base_reply = await self.ask(prompt)
        return f"{base_reply}\n\n{self.shop_url}\nwa.me/{self.whatsapp_number}"

    async def wa_reply(self, msg, history=""):
        prompt = f"""WhatsApp chat with customer. Goal: close the sale. Never greet first.
Use authentic Kenyan English/Sheng mix.
History: {history}
Customer: {msg}
Your reply:"""
        return await self.ask(prompt)
    
    async def generate_response(self, message, context=None):
        """Generate a response based on platform and context"""
        platform = context.get('platform', 'unknown') if context else 'unknown'
        
        if platform == 'whatsapp':
            history = context.get('history', '') if context else ''
            return await self.wa_reply(message, history)
        elif platform == 'facebook':
            return await self.fb_reply(message)
        else:
            prompt = f"""Generate a helpful reply to this message: {message}
Use authentic Kenyan English with some Sheng mix. Be friendly and helpful."""
            return await self.ask(prompt)
