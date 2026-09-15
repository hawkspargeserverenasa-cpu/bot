# ========== ULTIMATE SAFE 24/7 - BURST MODE - ALL TAGS - SESSION ID ==========
import asyncio
import aiohttp
import random
import os
import json
import hashlib
import uuid
from datetime import datetime

# ===== CONFIG =====
TARGETS = [
    "1515671401514930229",
    "1507363127111581741",
]
VOICE_ID = "1521453848428806164"
GUILD_ID = "1521416471396352181"
SPAM_CHANNEL = "1533271756389744961"
BURST_DELAY = 1
MAIN_DELAY = 10
BURST_COUNT = 3

# ===== FISIERE =====
TOKENS_FILE = "tokens.txt"
MSG_FILE = "file.txt"
SESSION_FILE = "session_data.json"

def load(file):
    if not os.path.exists(file):
        return []
    with open(file) as f:
        return [l.strip() for l in f if l.strip()]

TOKENS = load(TOKENS_FILE)
MESSAGES = load(MSG_FILE)

# ===== SESSION MANAGER =====
class SessionManager:
    def __init__(self):
        self.data = self.load()
        self.token_sessions = {}
    
    def load(self):
        try:
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE) as f:
                    d = json.load(f)
                last = datetime.fromisoformat(d.get("last_restart", "2000-01-01T00:00:00"))
                if (datetime.now() - last).total_seconds() > 86400:
                    return self.create()
                d["restart_count"] = d.get("restart_count", 0) + 1
                d["last_restart"] = datetime.now().isoformat()
                self.token_sessions = d.get("token_sessions", {})
                self.save(d)
                return d
            else:
                return self.create()
        except:
            return self.create()
    
    def create(self):
        d = {
            "session_id": hashlib.sha256(str(random.randint(0, 999999999)).encode()).hexdigest()[:32],
            "created_at": datetime.now().isoformat(),
            "restart_count": 1,
            "last_restart": datetime.now().isoformat(),
            "fingerprint": {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/{random.randint(122,129)}.0.0.0 Safari/537.36",
                "os": random.choice(["Windows", "macOS", "Linux"]),
                "locale": random.choice(["en-US", "en-GB", "ro-RO"])
            },
            "token_sessions": {}
        }
        self.token_sessions = {}
        self.save(d)
        return d
    
    def save(self, d=None):
        if not d:
            d = self.data
        d["token_sessions"] = self.token_sessions
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(d, f, indent=2)
        except:
            pass
    
    def get_id(self):
        return self.data.get("session_id", "unknown")
    
    def get_token_session(self, token):
        if token not in self.token_sessions:
            self.token_sessions[token] = hashlib.sha256((token + str(random.randint(0, 999999999))).encode()).hexdigest()[:16]
            self.save()
        return self.token_sessions[token]
    
    def get_fingerprint(self):
        return self.data.get("fingerprint", {})
    
    def get_restarts(self):
        return self.data.get("restart_count", 0)

session = SessionManager()

# ===== HEADERS =====
def gen_headers(token):
    fp = session.get_fingerprint()
    cv = f"{random.randint(122,129)}.0.{random.randint(0,9999)}.{random.randint(0,999)}"
    ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{cv} Safari/537.36"
    
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Language": f"{fp['locale']},en;q=0.9",
        "Origin": "https://discord.com",
        "Referer": "https://discord.com/channels/@me",
        "Sec-Ch-Ua": f'"Chromium";v="{cv.split(".")[0]}", "Google Chrome";v="{cv.split(".")[0]}", "Not?A_Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "X-Discord-Locale": fp["locale"],
        "X-Discord-Timezone": random.choice(["America/New_York", "Europe/London", "Europe/Bucharest"]),
        "X-Fingerprint": hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32],
        "X-Session-ID": session.get_token_session(token),
        "DNT": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

def vary(text):
    t = text.strip()
    if random.random() < 0.12: t = t.lower()
    if random.random() < 0.15: t = random.choice(['','> ','» ','• ']) + t
    if random.random() < 0.20: t = t + random.choice([' =))', ' =)))', ' =))))', ' =)))))', ' =))))))'])
    if random.random() < 0.04: t = t + '\u200b'
    return t[:2000]

# ===== SPAM WORKER =====
async def spam_worker(token, channel_id, token_num):
    ALL_TAGS = " ".join([f"<@{uid}>" for uid in TARGETS]) if TARGETS else ""
    
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://discord.com/api/v9/users/@me", headers=gen_headers(token)) as r:
                    if r.status != 200:
                        print(f"[T{token_num}] Token invalid, retrying in 30s...")
                        await asyncio.sleep(30)
                        continue
                    user = await r.json()
                    print(f"[T{token_num}] {user['username']} started | session: {session.get_token_session(token)[:8]}")
                
                i = 0
                while True:
                    try:
                        for b in range(BURST_COUNT):
                            msg = vary(MESSAGES[i % len(MESSAGES)])
                            i += 1
                            
                            if ALL_TAGS:
                                msg = f"{ALL_TAGS} {msg}"
                            
                            for attempt in range(3):
                                try:
                                    async with s.post(
                                        f"https://discord.com/api/v9/channels/{channel_id}/messages",
                                        headers=gen_headers(token),
                                        json={"content": msg},
                                        timeout=aiohttp.ClientTimeout(total=10)
                                    ) as r:
                                        if r.status == 200:
                                            print(f"[T{token_num}] ✓ {b+1}/{BURST_COUNT}")
                                            break
                                        elif r.status == 429:
                                            ra = (await r.json()).get("retry_after", 5)
                                            await asyncio.sleep(ra + 2)
                                        elif r.status == 403:
                                            print(f"[T{token_num}] No access to channel")
                                            await asyncio.sleep(60)
                                        else:
                                            await asyncio.sleep(3)
                                except:
                                    await asyncio.sleep(3)
                            
                            if b < BURST_COUNT - 1:
                                await asyncio.sleep(BURST_DELAY + random.uniform(-0.3, 0.3))
                        
                        await asyncio.sleep(MAIN_DELAY + random.uniform(-2, 2))
                        
                    except Exception as e:
                        print(f"[T{token_num}] Spam error: {e}")
                        await asyncio.sleep(10)
                        break
                        
        except Exception as e:
            print(f"[T{token_num}] Session error: {e}")
            await asyncio.sleep(10)

# ===== VOICE JOIN =====
async def join_voice(token, token_num):
    if not VOICE_ID or not GUILD_ID:
        return
    
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://discord.com/api/v9/gateway", headers=gen_headers(token)) as r:
                    if r.status != 200:
                        await asyncio.sleep(10)
                        continue
                    gw = await r.json()
                
                async with s.ws_connect(gw['url'] + "/?encoding=json&v=9") as ws:
                    hello = await ws.receive_json()
                    hb = hello['d']['heartbeat_interval'] / 1000
                    
                    async def heartbeat():
                        while True:
                            await asyncio.sleep(hb)
                            try:
                                await ws.send_json({"op": 1, "d": None})
                            except:
                                break
                    
                    hb_task = asyncio.create_task(heartbeat())
                    
                    await ws.send_json({"op": 2, "d": {
                        "token": token, "capabilities": 125829,
                        "properties": {
                            "os": "Windows", "browser": "Chrome", "device": "",
                            "system_locale": "en-US",
                            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "browser_version": "126.0.0.0", "os_version": "10",
                            "referrer": "", "referring_domain": "",
                            "referrer_current": "", "referring_domain_current": "",
                            "release_channel": "stable",
                            "client_build_number": 300000,
                            "client_event_source": None
                        },
                        "presence": {"status": "online", "since": 0, "activities": [], "afk": False},
                        "compress": False,
                        "client_state": {
                            "guild_versions": {}, "highest_last_message_id": "0",
                            "read_state_version": 0, "user_guild_settings_version": -1,
                            "user_settings_version": -1, "private_channels_version": "0",
                            "api_code_version": 0
                        }
                    }})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if json.loads(msg.data).get("t") == "READY":
                                break
                    
                    await ws.send_json({"op": 4, "d": {
                        "guild_id": GUILD_ID,
                        "channel_id": VOICE_ID,
                        "self_mute": True,
                        "self_deaf": False
                    }})
                    
                    print(f"[V{token_num}] Voice connected")
                    
                    while True:
                        try:
                            await asyncio.sleep(30)
                            await ws.send_json({"op": 4, "d": {
                                "guild_id": GUILD_ID,
                                "channel_id": VOICE_ID,
                                "self_mute": True,
                                "self_deaf": False
                            }})
                        except:
                            break
                    
                    hb_task.cancel()
                    
        except Exception as e:
            print(f"[V{token_num}] Voice disconnected: {e}, reconnecting...")
            await asyncio.sleep(10)

# ===== MAIN =====
async def main():
    if not TOKENS: return print("[ERROR] No tokens")
    if not MESSAGES: return print("[ERROR] No messages")
    if not SPAM_CHANNEL: return print("[ERROR] Set SPAM_CHANNEL")
    
    print("=" * 50)
    print(f"[SESSION] ID: {session.get_id()[:16]}...")
    print(f"[SESSION] Restarts: {session.get_restarts()}")
    print(f"[+] Tokens: {len(TOKENS)}")
    print(f"[+] Messages: {len(MESSAGES)}")
    print(f"[+] Targets: {len(TARGETS)} - ALL tagged")
    print(f"[+] Burst: {BURST_COUNT}msgs @ {BURST_DELAY}s | Pause: {MAIN_DELAY}s")
    print(f"[+] Voice: {VOICE_ID}")
    print(f"[+] Auto-reconnect: ON")
    print("=" * 50)
    
    tasks = []
    for num, token in enumerate(TOKENS, 1):
        tasks.append(asyncio.create_task(spam_worker(token, SPAM_CHANNEL, num)))
        if VOICE_ID and GUILD_ID:
            tasks.append(asyncio.create_task(join_voice(token, num)))
        await asyncio.sleep(2)
    
    print(f"[+] {len(TOKENS)} tokens active - 24/7")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[EXIT]")