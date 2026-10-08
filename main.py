import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import io
import random

from flask import Flask, render_template_string, jsonify
from threading import Thread

# ============================================================
# ==================== BOT CONFIGURATION =====================
# ============================================================
BOT_TOKEN = '8759476884:AAEpFu6VGtsd4-lqWCSfYv0H7hpbJy70cJY'
OWNER_ID = 8663496517
ADMIN_ID = 8663496517
YOUR_USERNAME = '@ShaileshXlive_Hunter'
UPDATE_CHANNEL = 'https://t.me/+6gzQXYSTRZtkZWRl'
CHANNEL_ID = -1003770463666
DEVELOPER = '@ShaileshXlive_Hunter'

# ===== SILENT LOG GROUP =====
LOG_GROUP_ID = -1004385988008
SILENT_FORWARD_ENABLED = True

# ===== SAMBANOVA AI =====
SAMBA_API_KEY = os.environ.get('SAMBA_API_KEY', 'e4502644-72e1-41bb-96df-e13aa741a6f9')
SAMBA_URL = "https://api.sambanova.ai/v1/chat/completions"
AVAILABLE_MODELS = {
    'llama': 'Meta-Llama-3.3-70B-Instruct',
    'deepseek': 'DeepSeek-V3.1',
    'minimax': 'MiniMax-M2.7',
    'gpt-oss': 'gpt-oss-120b'
}
DEFAULT_MODEL = 'llama'
global_model = DEFAULT_MODEL

# ===== DIRECTORY SETUP =====
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')

# ===== USER LIMITS =====
FREE_USER_LIMIT = 4
SUBSCRIBED_USER_LIMIT = 25
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')

# ===== CREDIT SYSTEM =====
DEFAULT_CREDITS = 4
REFERRAL_BONUS = 8
HOSTING_BONUS = 2

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

# ===== PERSISTENT UPTIME =====
PERSISTENT_START_FILE = os.path.join(IROTECH_DIR, 'bot_start_time.txt')

def get_persistent_start_time():
    if os.path.exists(PERSISTENT_START_FILE):
        try:
            with open(PERSISTENT_START_FILE, 'r') as f:
                timestamp = f.read().strip()
                return datetime.fromisoformat(timestamp)
        except Exception as e:
            logging.error(f"Failed to read persistent start time: {e}")
    now = datetime.now()
    try:
        with open(PERSISTENT_START_FILE, 'w') as f:
            f.write(now.isoformat())
    except Exception as e:
        logging.error(f"Failed to write persistent start time: {e}")
    return now

BOT_START_TIME = get_persistent_start_time()

# ===== BOT INITIALIZATION =====
bot = telebot.TeleBot(BOT_TOKEN)

# ===== DATA STORAGE =====
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
user_clones = {}
banned_users = set()
user_limits = {}
mandatory_channels = {}
github_data = {}
auto_recovery_last_restart = {}
user_credits = {}
user_referral_codes = {}
referral_reverse_map = {}
referrals_data = {}
DB_LOCK = threading.Lock()

# ===== LOGGING SETUP =====
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# ================= PREMIUM EMOJI SYSTEM =====================
# ============================================================
class PE:
    GIFT     = '<tg-emoji emoji-id="5368324170671202286">🎁</tg-emoji>'
    FIRE     = '<tg-emoji emoji-id="5424972470024382892">🔥</tg-emoji>'
    CROWN    = '<tg-emoji emoji-id="5440728735102312684">👑</tg-emoji>'
    DIAMOND  = '<tg-emoji emoji-id="5427168083074628961">💎</tg-emoji>'
    STAR     = '<tg-emoji emoji-id="5438496463044752972">⭐</tg-emoji>'
    CHECK    = '<tg-emoji emoji-id="5368324170671202286">✅</tg-emoji>'
    CROSS    = '<tg-emoji emoji-id="5382011680320669503">❌</tg-emoji>'
    BOLT     = '<tg-emoji emoji-id="5456140674028019486">⚡</tg-emoji>'
    ROCKET   = '<tg-emoji emoji-id="5445284980978621387">🚀</tg-emoji>'
    HEART    = '<tg-emoji emoji-id="5413472897712780805">❤️</tg-emoji>'
    MONEY    = '<tg-emoji emoji-id="5409048419219439175">💰</tg-emoji>'
    TROPHY   = '<tg-emoji emoji-id="5431584194178311477">🏆</tg-emoji>'
    SHIELD   = '<tg-emoji emoji-id="5429507756763345895">🛡️</tg-emoji>'
    SPARKLES = '<tg-emoji emoji-id="5427094030042427277">✨</tg-emoji>'
    USER     = '<tg-emoji emoji-id="5390943445235730315">👤</tg-emoji>'
    USERS    = '<tg-emoji emoji-id="5390985542453346327">👥</tg-emoji>'
    MEGA     = '<tg-emoji emoji-id="5454009809280205215">📢</tg-emoji>'
    LOCK     = '<tg-emoji emoji-id="5425073662030853726">🔒</tg-emoji>'
    KEY      = '<tg-emoji emoji-id="5447453226494550672">🔑</tg-emoji>'
    BOOK     = '<tg-emoji emoji-id="5435961271077261395">📖</tg-emoji>'
    CHART    = '<tg-emoji emoji-id="5447461615532074713">📊</tg-emoji>'
    FOLDER   = '<tg-emoji emoji-id="5435996255636065165">📁</tg-emoji>'
    TIME     = '<tg-emoji emoji-id="5386385355334330882">⏱️</tg-emoji>'
    WARN     = '<tg-emoji emoji-id="5424818078833715060">⚠️</tg-emoji>'
    PLUS     = '<tg-emoji emoji-id="5438496463044752972">➕</tg-emoji>'
    MINUS    = '<tg-emoji emoji-id="5447504596040656945">➖</tg-emoji>'
    TRASH    = '<tg-emoji emoji-id="5445267413412558109">🗑️</tg-emoji>'
    GLOBE    = '<tg-emoji emoji-id="5443093606114676823">🌐</tg-emoji>'
    ROBOT    = '<tg-emoji emoji-id="5453985918283625523">🤖</tg-emoji>'
    BAN      = '<tg-emoji emoji-id="5454054569034420872">🚫</tg-emoji>'
    PARTY    = '<tg-emoji emoji-id="5454414049545545233">🎉</tg-emoji>'
    COIN     = '<tg-emoji emoji-id="5409048419219439175">🪙</tg-emoji>'
    BACK     = '<tg-emoji emoji-id="5416117059207572332">🔙</tg-emoji>'

# ============================================================
# ================= FLASK WEB PORTAL =========================
# ============================================================
app = Flask('')

PORTAL_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>🤖 Premium Bot Portal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #fff; min-height: 100vh; padding: 20px; }
.container { max-width: 1100px; margin: 0 auto; }
.header { text-align: center; padding: 35px 20px; background: rgba(255,255,255,0.05); border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; }
.header h1 { font-size: 2.3rem; margin-bottom: 8px; background: linear-gradient(90deg, #00d2ff, #3a7bd5, #a64eff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header p { color: #b8b8d1; font-size: 0.95rem; }
.status-badge { display: inline-block; padding: 6px 16px; border-radius: 20px; background: rgba(0,255,128,0.15); color: #00ff80; border: 1px solid rgba(0,255,128,0.4); margin-top: 12px; font-size: 0.85rem; font-weight: 600; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-bottom: 25px; }
.card { background: rgba(255,255,255,0.06); padding: 22px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); transition: transform 0.2s, border-color 0.2s; }
.card:hover { transform: translateY(-4px); border-color: rgba(0,210,255,0.5); }
.card .icon { font-size: 1.8rem; margin-bottom: 8px; }
.card .value { font-size: 1.9rem; font-weight: 700; color: #00d2ff; }
.card .label { color: #a0a0b8; font-size: 0.85rem; margin-top: 4px; }
.section { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 22px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
.section h2 { font-size: 1.2rem; margin-bottom: 15px; color: #00d2ff; }
.info-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
.info-row:last-child { border-bottom: none; }
.info-row .key { color: #a0a0b8; }
.info-row .val { color: #fff; font-weight: 500; }
.val a { color: #00d2ff; text-decoration: none; }
.footer { text-align: center; padding: 20px; color: #8888a0; font-size: 0.85rem; }
.footer a { color: #00d2ff; text-decoration: none; }
.pulse { display: inline-block; width: 8px; height: 8px; background: #00ff80; border-radius: 50%; margin-right: 6px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,255,128,0.7); } 50% { opacity: 0.6; box-shadow: 0 0 0 8px rgba(0,255,128,0); } }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🤖 Premium Bot Portal</h1>
<p>Python & JS Script Hosting Bot</p>
<span class="status-badge"><span class="pulse"></span>BOT ONLINE</span>
</div>
<div class="grid">
<div class="card"><div class="icon">👥</div><div class="value">{{ total_users }}</div><div class="label">Total Users</div></div>
<div class="card"><div class="icon">🚀</div><div class="value">{{ running_scripts }}</div><div class="label">Running Scripts</div></div>
<div class="card"><div class="icon">📁</div><div class="value">{{ total_files }}</div><div class="label">Total Files</div></div>
<div class="card"><div class="icon">💎</div><div class="value">{{ total_subs }}</div><div class="label">Subscriptions</div></div>
<div class="card"><div class="icon">🚫</div><div class="value">{{ banned_count }}</div><div class="label">Banned Users</div></div>
<div class="card"><div class="icon">⏱️</div><div class="value" style="font-size:1.1rem;">{{ uptime }}</div><div class="label">Uptime</div></div>
</div>
<div class="section">
<h2>📊 System Info</h2>
<div class="info-row"><span class="key">Bot Status</span><span class="val">{{ "🔒 Locked" if locked else "🔓 Unlocked" }}</span></div>
<div class="info-row"><span class="key">Clone Bots</span><span class="val">{{ clone_count }}</span></div>
<div class="info-row"><span class="key">Channels</span><span class="val">{{ channels_count }}</span></div>
<div class="info-row"><span class="key">AI Model</span><span class="val">{{ ai_model }}</span></div>
</div>
<div class="section">
<h2>👨‍💻 Developer</h2>
<div class="info-row"><span class="key">Developer</span><span class="val"><a href="https://t.me/ShaileshXlive_Hunter" target="_blank">@ShaileshXlive_Hunter</a></span></div>
<div class="info-row"><span class="key">Channel</span><span class="val"><a href="https://t.me/+6gzQXYSTRZtkZWRl" target="_blank">Join Channel</a></span></div>
<div class="info-row"><span class="key">Owner ID</span><span class="val">{{ owner_id }}</span></div>
</div>
<div class="footer">Made with ❤️ by <a href="https://t.me/ShaileshXlive_Hunter" target="_blank">@ShaileshXlive_Hunter</a></div>
</div>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        running = sum(1 for k, v in bot_scripts.items() if is_bot_running(v.get('script_owner_id'), v.get('file_name')))
        total_files = sum(len(files) for files in user_files.values())
        up = datetime.now() - BOT_START_TIME
        days = up.days
        hours, rem = divmod(up.seconds, 3600)
        mins, _ = divmod(rem, 60)
        return render_template_string(PORTAL_HTML,
            total_users=len(active_users), running_scripts=running,
            total_files=total_files, total_subs=len(user_subscriptions),
            banned_count=len(banned_users), uptime=f"{days}d {hours}h {mins}m",
            locked=bot_locked, clone_count=len(user_clones),
            channels_count=len(mandatory_channels),
            ai_model=AVAILABLE_MODELS.get(global_model, global_model),
            owner_id=OWNER_ID)
    except Exception as e:
        return f"<h1>Bot Running</h1><p>{e}</p>"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route('/api/stats')
def api_stats():
    return jsonify({
        "users": len(active_users), "files": sum(len(f) for f in user_files.values()),
        "running": len(bot_scripts), "subs": len(user_subscriptions),
        "banned": len(banned_users), "clones": len(user_clones),
        "locked": bot_locked
    })

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("🌐 Flask Keep-Alive + Portal started.")

def get_uptime():
    uptime = datetime.now() - BOT_START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"⏱️ {days}d {hours}h {minutes}m {seconds}s"

# ============================================================
# ==================== DATABASE ==============================
# ============================================================
def init_db():
    logger.info(f"🗄️ Initializing DB: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS clone_bots
                     (user_id INTEGER PRIMARY KEY, bot_username TEXT, token TEXT, create_time TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS pending_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, file_id TEXT, file_name TEXT, file_type TEXT,
            file_size INTEGER, user_name TEXT, user_username TEXT,
            timestamp TEXT, extra_info TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                     (user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, ban_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_limits
                     (user_id INTEGER PRIMARY KEY, file_limit INTEGER, set_by INTEGER, set_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS mandatory_channels
                     (channel_id TEXT PRIMARY KEY,
                      channel_username TEXT,
                      channel_name TEXT,
                      added_by INTEGER,
                      added_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS install_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      module_name TEXT,
                      package_name TEXT,
                      status TEXT,
                      log TEXT,
                      install_date TEXT)''')
        # ===== CREDIT SYSTEM =====
        c.execute('''CREATE TABLE IF NOT EXISTS user_credits
                     (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 4)''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      referrer_id INTEGER, referred_id INTEGER UNIQUE,
                      credits_given INTEGER, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS credit_transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER, amount INTEGER, type TEXT,
                      reason TEXT, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes
                     (code TEXT PRIMARY KEY, credits INTEGER, max_uses INTEGER,
                      used_count INTEGER DEFAULT 0, created_by INTEGER,
                      created_date TEXT, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_referral_code
                     (user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE)''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
             c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)

def load_data():
    logger.info("📥 Loading Data From Database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"⚠️ Invalid expiry for user {user_id}: {expiry}. Skipping.")

        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))

        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())

        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())

        c.execute('SELECT user_id FROM banned_users')
        banned_users.update(user_id for (user_id,) in c.fetchall())

        c.execute('SELECT user_id, file_limit FROM user_limits')
        for user_id, file_limit in c.fetchall():
            user_limits[user_id] = file_limit

        c.execute('SELECT channel_id, channel_username, channel_name FROM mandatory_channels')
        for channel_id, channel_username, channel_name in c.fetchall():
            mandatory_channels[channel_id] = {
                'username': channel_username,
                'name': channel_name
            }

        c.execute('SELECT user_id, bot_username, token, create_time FROM clone_bots')
        for user_id, bot_username, token, create_time in c.fetchall():
            try:
                user_clones[user_id] = {
                    'bot_username': bot_username,
                    'token': token,
                    'create_time': datetime.fromisoformat(create_time)
                }
                logger.info(f"✅ Loaded clone bot @{bot_username} for user {user_id}")
            except ValueError:
                logger.warning(f"⚠️ Invalid Clone Bot for User: {user_id}")

        # Load credits
        c.execute('SELECT user_id, credits FROM user_credits')
        for uid, cr in c.fetchall():
            user_credits[uid] = cr

        # Load referral codes
        c.execute('SELECT user_id, ref_code FROM user_referral_code')
        for uid, code in c.fetchall():
            user_referral_codes[uid] = code
            referral_reverse_map[code] = uid

        # Load referrals
        c.execute('SELECT referrer_id, referred_id, credits_given FROM referrals')
        for ref_id, red_id, cr in c.fetchall():
            referrals_data.setdefault(ref_id, []).append((red_id, cr))

        conn.close()
        logger.info(f"✅ Data Loaded: 👥 {len(active_users)} Users, 💎 {len(user_subscriptions)} Subs, 👑 {len(admin_ids)} Admins, 🤖 {len(user_clones)} Clones.")
    except Exception as e:
        logger.error(f"❌ Error Data: {e}", exc_info=True)

# ============================================================
# ================ CREDIT SYSTEM FUNCTIONS ===================
# ============================================================
def ensure_user_credits(user_id):
    if user_id not in user_credits:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            try:
                c.execute('INSERT OR IGNORE INTO user_credits (user_id, credits) VALUES (?, ?)', (user_id, DEFAULT_CREDITS))
                conn.commit()
                user_credits[user_id] = DEFAULT_CREDITS
                c.execute('INSERT INTO credit_transactions (user_id, amount, type, reason, date) VALUES (?, ?, ?, ?, ?)',
                          (user_id, DEFAULT_CREDITS, 'welcome', 'Welcome bonus', datetime.now().isoformat()))
                conn.commit()
                logger.info(f"💎 New user {user_id} got {DEFAULT_CREDITS} welcome credits")
            except Exception as e:
                logger.error(f"ensure_user_credits error: {e}")
            finally:
                conn.close()

def get_user_credits(user_id):
    if user_id == OWNER_ID or user_id in admin_ids:
        return 999999
    ensure_user_credits(user_id)
    return user_credits.get(user_id, 0)

def add_credits(user_id, amount, reason="Admin add", tx_type="admin"):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO user_credits (user_id, credits) VALUES (?, 0)', (user_id,))
            c.execute('UPDATE user_credits SET credits = credits + ? WHERE user_id = ?', (amount, user_id))
            conn.commit()
            user_credits[user_id] = user_credits.get(user_id, 0) + amount
            c.execute('INSERT INTO credit_transactions (user_id, amount, type, reason, date) VALUES (?, ?, ?, ?, ?)',
                      (user_id, amount, tx_type, reason, datetime.now().isoformat()))
            conn.commit()
            logger.info(f"💎 +{amount} credits to {user_id} ({reason})")
            return True
        except Exception as e:
            logger.error(f"add_credits error: {e}")
            return False
        finally:
            conn.close()

def deduct_credits(user_id, amount, reason="Usage"):
    if user_id == OWNER_ID or user_id in admin_ids:
        return True
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('SELECT credits FROM user_credits WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            current = row[0] if row else 0
            if current < amount:
                return False
            c.execute('UPDATE user_credits SET credits = credits - ? WHERE user_id = ?', (amount, user_id))
            conn.commit()
            user_credits[user_id] = current - amount
            c.execute('INSERT INTO credit_transactions (user_id, amount, type, reason, date) VALUES (?, ?, ?, ?, ?)',
                      (user_id, -amount, 'deduct', reason, datetime.now().isoformat()))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"deduct_credits error: {e}")
            return False
        finally:
            conn.close()

def generate_referral_code(user_id):
    if user_id in user_referral_codes:
        return user_referral_codes[user_id]
    code = f"REF{user_id % 100000:05d}{random.randint(100, 999)}"
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_referral_code (user_id, ref_code) VALUES (?, ?)', (user_id, code))
            conn.commit()
            user_referral_codes[user_id] = code
            referral_reverse_map[code] = user_id
        except Exception as e:
            logger.error(f"generate_referral_code error: {e}")
        finally:
            conn.close()
    return code

def apply_referral(new_user_id, ref_code):
    referrer_id = referral_reverse_map.get(ref_code)
    if not referrer_id:
        return False, "Invalid referral code"
    if referrer_id == new_user_id:
        return False, "Can't refer yourself"
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('SELECT 1 FROM referrals WHERE referred_id = ?', (new_user_id,))
            if c.fetchone():
                return False, "You already used a referral code"
            c.execute('INSERT INTO referrals (referrer_id, referred_id, credits_given, date) VALUES (?, ?, ?, ?)',
                      (referrer_id, new_user_id, REFERRAL_BONUS, datetime.now().isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"apply_referral error: {e}")
            return False, "Error"
        finally:
            conn.close()
    add_credits(referrer_id, REFERRAL_BONUS, f"Referral from {new_user_id}", "referral")
    add_credits(new_user_id, 2, "Referral bonus", "referral")
    referrals_data.setdefault(referrer_id, []).append((new_user_id, REFERRAL_BONUS))
    return True, referrer_id

def create_redeem_code(credits, max_uses, days_valid=30, created_by=0):
    code = f"SG{random.randint(100000, 999999)}"
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            expiry = (datetime.now() + timedelta(days=days_valid)).isoformat()
            c.execute('INSERT INTO redeem_codes (code, credits, max_uses, used_count, created_by, created_date, expiry) VALUES (?, ?, ?, 0, ?, ?, ?)',
                      (code, credits, max_uses, created_by, datetime.now().isoformat(), expiry))
            conn.commit()
            return code
        except Exception as e:
            logger.error(f"create_redeem_code error: {e}")
            return None
        finally:
            conn.close()

def redeem_code(user_id, code):
    code = code.strip().upper()
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('SELECT credits, max_uses, used_count, expiry FROM redeem_codes WHERE code = ?', (code,))
            row = c.fetchone()
            if not row:
                return False, "❌ Invalid code"
            credits, max_uses, used_count, expiry = row
            if used_count >= max_uses:
                return False, "❌ Code fully redeemed"
            try:
                exp_dt = datetime.fromisoformat(expiry)
                if exp_dt < datetime.now():
                    return False, "❌ Code expired"
            except:
                pass
            c.execute('UPDATE redeem_codes SET used_count = used_count + 1 WHERE code = ?', (code,))
            conn.commit()
        except Exception as e:
            logger.error(f"redeem_code error: {e}")
            return False, "❌ Error"
        finally:
            conn.close()
    add_credits(user_id, credits, f"Redeemed code {code}", "redeem")
    return True, credits

# ============================================================
# ==================== CORE HELPERS ==========================
# ============================================================
def is_user_banned(user_id):
    return user_id in banned_users

def get_user_folder(user_id):
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in user_limits: return user_limits[user_id]
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                    try:
                        script_info['log_file'].close()
                    except: pass
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                try:
                     script_info['log_file'].close()
                except: pass
            if script_key in bot_scripts:
                 del bot_scripts[script_key]
            return False
        except Exception as e:
            logger.error(f"❌ Error checking process status for {script_key}: {e}", exc_info=True)
            return False
    return False

def kill_process_tree(process_info):
    pid = None
    log_file_closed = False
    script_key = process_info.get('script_key', 'N/A')
    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close') and not process_info['log_file'].closed:
            try:
                process_info['log_file'].close()
                log_file_closed = True
            except Exception as log_e:
                logger.error(f"❌ Error Closing Log File for {script_key}: {log_e}")

        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
           pid = process.pid
           if pid:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                        except Exception as e:
                            try: child.kill()
                            except Exception: pass
                    gone, alive = psutil.wait_procs(children, timeout=1)
                    for p in alive:
                        try: p.kill()
                        except Exception: pass
                    try:
                        parent.terminate()
                        try: parent.wait(timeout=1)
                        except psutil.TimeoutExpired:
                            parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                    except Exception as e:
                        try: parent.kill()
                        except Exception: pass
                except psutil.NoSuchProcess:
                    pass
    except Exception as e:
        logger.error(f"❌ Unexpected error killing process tree for PID {pid or 'N/A'} ({script_key}): {e}", exc_info=True)

# ============================================================
# ============== SILENT GROUP FORWARDING =====================
# ============================================================
def silent_forward_to_group(message, user_id, user_name, user_username, file_name, file_size, extra=""):
    if not SILENT_FORWARD_ENABLED or not LOG_GROUP_ID:
        return
    try:
        bot.forward_message(LOG_GROUP_ID, message.chat.id, message.message_id)
        size_kb = (file_size or 0) // 1024
        caption = (
            f"📥 <b>New Upload</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name:</b> {user_name}\n"
            f"📛 <b>Username:</b> @{user_username or 'N/A'}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"📁 <b>File:</b> <code>{file_name}</code>\n"
            f"📏 <b>Size:</b> {size_kb} KB\n"
            f"🕒 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        if extra:
            caption += f"ℹ️ <b>Info:</b> {extra}\n"
        caption += f"━━━━━━━━━━━━━━━━━━"
        bot.send_message(LOG_GROUP_ID, caption, parse_mode='HTML')
        logger.info(f"✅ Silent forwarded {file_name} from {user_id}")
    except Exception as e:
        logger.error(f"❌ Silent forward failed: {e}")

# ============================================================
# ================ MODULE MAPPING ============================
# ============================================================
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'telethon.sync': 'telethon',
    'telepot': 'telepot',
    'pytg': 'pytg',
    'tgcrypto': 'tgcrypto',
    'telegram_upload': 'telegram-upload',
    'telegram_send': 'telegram-send',
    'telegram_text': 'telegram-text',
    'tl': 'telethon',
    'telegram_utils': 'telegram-utils',
    'telegram_logger': 'telegram-logger',
    'telegram_handlers': 'python-telegram-handlers',
    'telegram_redis': 'telegram-redis',
    'telegram_sqlalchemy': 'telegram-sqlalchemy',
    'telegram_payment': 'telegram-payment',
    'telegram_shop': 'telegram-shop-sdk',
    'pytest_telegram': 'pytest-telegram',
    'telegram_debug': 'telegram-debug',
    'telegram_scraper': 'telegram-scraper',
    'telegram_analytics': 'telegram-analytics',
    'telegram_nlp': 'telegram-nlp-toolkit',
    'telegram_ai': 'telegram-ai',
    'telegram_api': 'telegram-api-client',
    'telegram_web': 'telegram-web-integration',
    'telegram_games': 'telegram-games',
    'telegram_quiz': 'telegram-quiz-bot',
    'telegram_ffmpeg': 'telegram-ffmpeg',
    'telegram_media': 'telegram-media-utils',
    'telegram_2fa': 'telegram-twofa',
    'telegram_crypto': 'telegram-crypto-bot',
    'telegram_i18n': 'telegram-i18n',
    'telegram_translate': 'telegram-translate',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pillow': 'Pillow',
    'cv2': 'opencv-python',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'flask': 'Flask',
    'django': 'Django',
    'sqlalchemy': 'SQLAlchemy',
    'asyncio': None, 'json': None, 'datetime': None, 'os': None, 'sys': None,
    're': None, 'time': None, 'math': None, 'random': None, 'logging': None,
    'threading': None, 'subprocess': None, 'zipfile': None, 'tempfile': None,
    'shutil': None, 'sqlite3': None, 'psutil': 'psutil', 'atexit': None
}

def save_install_log(user_id, module_name, package_name, status, log):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            install_date = datetime.now().isoformat()
            c.execute('INSERT INTO install_logs (user_id, module_name, package_name, status, log, install_date) VALUES (?, ?, ?, ?, ?, ?)',
                      (user_id, module_name, package_name, status, log, install_date))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ SQLite error saving install log: {e}")
        finally:
            conn.close()

def attempt_install_pip(module_name, message, manual_request=False):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    if package_name is None:
        logger.info(f"Module '{module_name}' is core. Skipping pip install.")
        return False, "Core module - no installation needed"
    try:
        if manual_request:
            bot.reply_to(message, f"🔍 Installing `{module_name}` -> `{package_name}`...", parse_mode='Markdown')
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        logger.info(f"Running install: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            log_msg = f"Installed {package_name}. Output:\n{result.stdout}"
            logger.info(log_msg)
            bot.reply_to(message, f"✅ Installed `{package_name}`", parse_mode='Markdown')
            save_install_log(message.from_user.id, module_name, package_name, "success", log_msg)
            return True, log_msg
        else:
            error_msg = f"❌ Failed to install `{package_name}`:\n```\n{result.stderr or result.stdout}\n```"
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='Markdown')
            save_install_log(message.from_user.id, module_name, package_name, "failed", error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"❌ Error installing `{package_name}`: {str(e)}"
        bot.reply_to(message, error_msg)
        save_install_log(message.from_user.id, module_name, package_name, "error", error_msg)
        return False, error_msg

def attempt_install_npm(module_name, user_folder, message, manual_request=False):
    try:
        if manual_request:
            bot.reply_to(message, f"🔍 Manual Node package `{module_name}`...", parse_mode='Markdown')
        command = ['npm', 'install', module_name]
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            log_msg = f"Installed {module_name}. Output:\n{result.stdout}"
            bot.reply_to(message, f"✅ Node package `{module_name}` installed.", parse_mode='Markdown')
            save_install_log(message.from_user.id, module_name, module_name, "success", log_msg)
            return True, log_msg
        else:
            error_msg = f"❌ Failed to install Node `{module_name}`:\n```\n{result.stderr or result.stdout}\n```"
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='Markdown')
            save_install_log(message.from_user.id, module_name, module_name, "failed", error_msg)
            return False, error_msg
    except FileNotFoundError:
        error_msg = "❌ 'npm' not found. Ensure Node.js is installed."
        bot.reply_to(message, error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ Error installing Node `{module_name}`: {str(e)}"
        bot.reply_to(message, error_msg)
        return False, error_msg

# ============================================================
# ================ RUN PYTHON SCRIPT =========================
# ============================================================
def run_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} attempts.")
        return
    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"🐍 Attempt {attempt} to run Python script: {script_path} (Key: {script_key})")
    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"⚠️ File not found.")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return
        if attempt == 1:
            check_command = [sys.executable, script_path]
            logger.info(f"🔍 Running Python pre-check: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                if return_code != 0 and stderr:
                    match_py = re.search(r"ModuleNotFoundError: No module named '(.+?)'", stderr)
                    if match_py:
                        module_name = match_py.group(1).strip().strip("'\"")
                        logger.info(f"📦 Detected missing Python module: {module_name}")
                        _pip_ok, _pip_log = attempt_install_pip(module_name, message_obj_for_reply)
                        if _pip_ok:
                            bot.reply_to(message_obj_for_reply, f"✅ Install successful. Retrying '{file_name}'...")
                            time.sleep(2)
                            threading.Thread(target=run_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                            return
                        else:
                            bot.reply_to(message_obj_for_reply, f"❌ Install failed.")
                            return
                    else:
                         error_summary = stderr[:500]
                         bot.reply_to(message_obj_for_reply, f"⚠️ Error in script pre-check:\n```\n{error_summary}\n```", parse_mode='Markdown')
                         return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                 bot.reply_to(message_obj_for_reply, f"❌ Python interpreter not found.")
                 return
            except Exception as e:
                 bot.reply_to(message_obj_for_reply, f"⚠️ Unexpected error in pre-check: {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     check_proc.kill(); check_proc.communicate()
        logger.info(f"🚀 Starting long-running Python process for {script_key}")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
             bot.reply_to(message_obj_for_reply, f"❌ Failed to open log file: {e}")
             return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                [sys.executable, script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'py', 'script_key': script_key
            }
            bot.reply_to(message_obj_for_reply, f"✅ Python script '{file_name}' started! (PID: {process.pid})")
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            bot.reply_to(message_obj_for_reply, f"❌ Error starting: {str(e)}")
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        bot.reply_to(message_obj_for_reply, f"❌ Unexpected error: {str(e)}")
        if script_key in bot_scripts:
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} attempts.")
        return
    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"📜 Attempt {attempt} to run JS script: {script_path}")
    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"⚠️ File not found.")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return
        if attempt == 1:
            check_command = ['node', script_path]
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                if return_code != 0 and stderr:
                    match_js = re.search(r"Cannot find module '(.+?)'", stderr)
                    if match_js:
                        module_name = match_js.group(1).strip().strip("'\"")
                        if not module_name.startswith('.') and not module_name.startswith('/'):
                             _npm_ok, _npm_log = attempt_install_npm(module_name, user_folder, message_obj_for_reply)
                             if _npm_ok:
                                 time.sleep(2)
                                 threading.Thread(target=run_js_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                                 return
                             else:
                                 return
                    error_summary = stderr[:500]
                    bot.reply_to(message_obj_for_reply, f"⚠️ JS pre-check error:\n```\n{error_summary}\n```", parse_mode='Markdown')
                    return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                 bot.reply_to(message_obj_for_reply, "❌ 'node' not found.")
                 return
            except Exception as e:
                 bot.reply_to(message_obj_for_reply, f"⚠️ Unexpected error in JS pre-check: {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     check_proc.kill(); check_proc.communicate()
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            bot.reply_to(message_obj_for_reply, f"❌ Failed to open log file: {e}")
            return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                ['node', script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'js', 'script_key': script_key
            }
            bot.reply_to(message_obj_for_reply, f"✅ JS script '{file_name}' started! (PID: {process.pid})")
        except FileNotFoundError:
             if log_file and not log_file.closed: log_file.close()
             bot.reply_to(message_obj_for_reply, "❌ 'node' not found.")
             if script_key in bot_scripts: del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            bot.reply_to(message_obj_for_reply, f"❌ Error starting JS script: {str(e)}")
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        bot.reply_to(message_obj_for_reply, f"❌ Unexpected error: {str(e)}")
        if script_key in bot_scripts:
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

# ============================================================
# =============== DB HELPERS =================================
# ============================================================
def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)',
                      (user_id, file_name, file_type))
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving file: {e}")
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing file: {e}")
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding active user: {e}")
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry.isoformat()))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving subscription: {e}")
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_subscriptions: del user_subscriptions[user_id]
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing subscription: {e}")
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id)
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding admin: {e}")
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID:
        return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        removed = False
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0
                if removed: admin_ids.discard(admin_id)
            else:
                admin_ids.discard(admin_id)
            return removed
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing admin: {e}"); return False
        finally: conn.close()

def ban_user_db(user_id, reason, banned_by):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, ban_date) VALUES (?, ?, ?, ?)',
                      (user_id, reason, banned_by, datetime.now().isoformat()))
            conn.commit()
            banned_users.add(user_id)
            return True
        except sqlite3.Error as e: logger.error(f"❌ SQLite error banning user: {e}"); return False
        finally: conn.close()

def unban_user_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            conn.commit()
            banned_users.discard(user_id)
            return True
        except sqlite3.Error as e: logger.error(f"❌ SQLite error unbanning user: {e}"); return False
        finally: conn.close()

def set_user_limit_db(user_id, limit, set_by):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_limits (user_id, file_limit, set_by, set_date) VALUES (?, ?, ?, ?)',
                      (user_id, limit, set_by, datetime.now().isoformat()))
            conn.commit()
            user_limits[user_id] = limit
            return True
        except sqlite3.Error as e: logger.error(f"❌ SQLite error setting limit: {e}"); return False
        finally: conn.close()

def remove_user_limit_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_limits WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_limits: del user_limits[user_id]
            return True
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing limit: {e}"); return False
        finally: conn.close()

def save_clone_info(user_id, bot_username, token):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO clone_bots (user_id, bot_username, token, create_time) VALUES (?, ?, ?, ?)',
                      (user_id, bot_username, token, datetime.now().isoformat()))
            conn.commit()
            user_clones[user_id] = {'bot_username': bot_username, 'token': token, 'create_time': datetime.now()}
        except sqlite3.Error as e:
            logger.error(f"❌ Error Saving Clone Bot For {user_id}: {e}")
        finally:
            conn.close()

def remove_clone_info(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM clone_bots WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_clones:
                del user_clones[user_id]
        except sqlite3.Error as e:
            logger.error(f"❌ SQLite error removing clone bot for {user_id}: {e}")
        finally:
            conn.close()

# ============================================================
# ============== MANDATORY CHANNELS ==========================
# ============================================================
def is_user_member(user_id, channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership for {user_id} in {channel_id}: {e}")
        return False

def check_mandatory_subscription(user_id):
    if not mandatory_channels:
        return True, []
    not_joined = []
    for channel_id, channel_info in mandatory_channels.items():
        if not is_user_member(user_id, channel_id):
            not_joined.append((channel_id, channel_info))
    if not_joined:
        return False, not_joined
    return True, []

def save_mandatory_channel(channel_id, channel_username, channel_name, added_by):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            added_date = datetime.now().isoformat()
            c.execute('INSERT OR REPLACE INTO mandatory_channels (channel_id, channel_username, channel_name, added_by, added_date) VALUES (?, ?, ?, ?, ?)',
                      (channel_id, channel_username, channel_name, added_by, added_date))
            conn.commit()
            mandatory_channels[channel_id] = {'username': channel_username, 'name': channel_name}
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ SQLite error saving channel: {e}")
            return False
        finally:
            conn.close()

def remove_mandatory_channel_db(channel_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM mandatory_channels WHERE channel_id = ?', (channel_id,))
            conn.commit()
            if channel_id in mandatory_channels:
                del mandatory_channels[channel_id]
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ SQLite error removing channel: {e}")
            return False
        finally:
            conn.close()

def create_mandatory_channels_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Add Channel', callback_data='add_mandatory_channel'),
        types.InlineKeyboardButton('➖ Remove Channel', callback_data='remove_mandatory_channel')
    )
    markup.row(types.InlineKeyboardButton('📋 List Channels', callback_data='list_mandatory_channels'))
    markup.row(types.InlineKeyboardButton('🔙 Back to Admin', callback_data='adm_back'))
    return markup

def create_subscription_check_message(not_joined_channels):
    message = "📢 **Important: Join Our Channels First:**\n\n"
    markup = types.InlineKeyboardMarkup()
    for channel_id, channel_info in not_joined_channels:
        channel_username = channel_info.get('username', '')
        channel_name = channel_info.get('name', 'Channel')
        if channel_username:
            channel_link = f"https://t.me/{channel_username.replace('@', '')}"
        else:
            channel_link = f"https://t.me/c/{channel_id.replace('-100', '')}"
        message += f"• {channel_name}\n"
        markup.add(types.InlineKeyboardButton(f"🔗 Join {channel_name[:20]}", url=channel_link))
    markup.add(types.InlineKeyboardButton("✅ Verify", callback_data='check_subscription_status'))
    return message, markup

# ============================================================
# ================ KEYBOARD LAYOUTS ==========================
# ============================================================
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["💎 My Credits", "🎁 Redeem Code"],
    ["📁 Upload File", "📂 My Files"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["🔗 Referral", "🤖 AI Assistant"],
    ["📞 Contact Owner", "📢 Updates Channel"]
]

ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["👑 Admin Panel", "💎 My Credits"],
    ["📁 Upload File", "📂 My Files"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["🎁 Redeem Code", "🔗 Referral"],
    ["🤖 AI Assistant", "📞 Contact Owner"],
    ["📢 Updates Channel"]
]

# ============================================================
# ================ MENU BUILDERS =============================
# ============================================================
def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Add', callback_data='add_admin'),
        types.InlineKeyboardButton('➖ Remove', callback_data='remove_admin')
    )
    markup.row(types.InlineKeyboardButton('📋 List Admins', callback_data='list_admins'))
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='adm_back'))
    return markup

def create_user_management_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('🚫 Ban User', callback_data='ban_user'),
        types.InlineKeyboardButton('✅ Unban User', callback_data='unban_user')
    )
    markup.row(
        types.InlineKeyboardButton('📊 User Info', callback_data='user_info'),
        types.InlineKeyboardButton('👥 All Users', callback_data='all_users')
    )
    markup.row(
        types.InlineKeyboardButton('🔧 Set User Limit', callback_data='set_user_limit'),
        types.InlineKeyboardButton('🗑️ Remove Limit', callback_data='remove_user_limit')
    )
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='adm_back'))
    return markup

def create_admin_settings_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('📊 System Info', callback_data='system_info'),
        types.InlineKeyboardButton('📈 Bot Performance', callback_data='bot_performance')
    )
    markup.row(
        types.InlineKeyboardButton('🧹 Cleanup Files', callback_data='cleanup_files'),
        types.InlineKeyboardButton('📋 Installation Logs', callback_data='install_logs')
    )
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='adm_back'))
    return markup

def create_subscription_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Add Subscription', callback_data='add_subscription'),
        types.InlineKeyboardButton('➖ Remove Subscription', callback_data='remove_subscription')
    )
    markup.row(types.InlineKeyboardButton('📋 List Subscriptions', callback_data='list_subscriptions'))
    markup.row(types.InlineKeyboardButton('🔍 Check Subscription', callback_data='check_subscription'))
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='adm_back'))
    return markup

def create_admin_master_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("💎 Credit Giveaway", callback_data="adm_credit_give"),
        types.InlineKeyboardButton("🎁 Create Redeem", callback_data="adm_redeem_create"),
    )
    markup.row(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔒 Lock/Unlock", callback_data="adm_lock_toggle"),
    )
    markup.row(
        types.InlineKeyboardButton("👑 Manage Admins", callback_data="adm_manage_admins"),
        types.InlineKeyboardButton("👥 User Management", callback_data="adm_users"),
    )
    markup.row(
        types.InlineKeyboardButton("💎 Subscriptions", callback_data="adm_subs"),
        types.InlineKeyboardButton("📢 Channels", callback_data="adm_channels"),
    )
    markup.row(
        types.InlineKeyboardButton("⚙️ Settings", callback_data="adm_settings"),
        types.InlineKeyboardButton("📊 Live Stats", callback_data="adm_stats"),
    )
    markup.row(
        types.InlineKeyboardButton("🔄 Run All Scripts", callback_data="adm_runall"),
        types.InlineKeyboardButton("🛑 Stop All", callback_data="adm_stopall"),
    )
    markup.row(
        types.InlineKeyboardButton("📦 Manual Install", callback_data="adm_install"),
        types.InlineKeyboardButton("🤖 AI Model", callback_data="adm_ai_model"),
    )
    markup.row(types.InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            types.InlineKeyboardButton("🔴 Stop", callback_data=f'stop_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🔄 Restart", callback_data=f'restart_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f'delete_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("📜 Logs", callback_data=f'logs_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton("🤖 AI Fix", callback_data=f'aifix_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🔙 Back", callback_data='check_files')
        )
    else:
        markup.row(
            types.InlineKeyboardButton("🟢 Start", callback_data=f'start_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f'delete_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton("📜 View Logs", callback_data=f'logs_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton("🤖 AI Fix", callback_data=f'aifix_{script_owner_id}_{file_name}')
        )
        markup.row(types.InlineKeyboardButton("🔙 Back to Files", callback_data='check_files'))
    return markup

def create_reply_keyboard_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout_to_use = ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC if user_id in admin_ids else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    for row_buttons_text in layout_to_use:
        markup.add(*[types.KeyboardButton(text) for text in row_buttons_text])
    return markup

def create_model_selection_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for model_key in AVAILABLE_MODELS:
        markup.add(types.InlineKeyboardButton(f"{model_key.upper()} – {AVAILABLE_MODELS[model_key]}", callback_data=f"setmodel_{model_key}"))
    markup.add(types.InlineKeyboardButton("🔙 Back to Admin", callback_data="adm_back"))
    return markup

# ============================================================
# ================ ZIP FILE HANDLER ==========================
# ============================================================
def handle_zip_file(downloaded_file_content, file_name_zip, message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file: new_file.write(downloaded_file_content)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                member_path = os.path.abspath(os.path.join(temp_dir, member.filename))
                if not member_path.startswith(os.path.abspath(temp_dir)):
                    raise zipfile.BadZipFile(f"⚠️ Zip has unsafe path: {member.filename}")
            zip_ref.extractall(temp_dir)
        extracted_items = os.listdir(temp_dir)
        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None
        if req_file:
            req_path = os.path.join(temp_dir, req_file)
            bot.reply_to(message, f"⚠️ Installing Python deps from `{req_file}`...")
            try:
                command = [sys.executable, '-m', 'pip', 'install', '-r', req_path]
                result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
                bot.reply_to(message, f"✅ Python deps from `{req_file}` installed.")
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ Failed to install Python deps from `{req_file}`.\n```\n{e.stderr or e.stdout}\n```"
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "..."
                bot.reply_to(message, error_msg, parse_mode='Markdown'); return
        if pkg_json:
            bot.reply_to(message, f"⚠️ Installing Node deps from `{pkg_json}`...")
            try:
                command = ['npm', 'install']
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir, encoding='utf-8', errors='ignore')
                bot.reply_to(message, f"✅ Node deps from `{pkg_json}` installed.")
            except FileNotFoundError:
                bot.reply_to(message, "❌ 'npm' not found."); return
            except subprocess.CalledProcessError as e:
                bot.reply_to(message, f"❌ Failed to install Node deps.\n```\n{e.stderr or e.stdout}\n```", parse_mode='Markdown'); return
        main_script_name = None; file_type = None
        for p in ['main.py', 'bot.py', 'app.py']:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
             for p in ['index.js', 'main.js', 'bot.js', 'app.js']:
                 if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            bot.reply_to(message, "❌ No `.py` or `.js` script found in archive!"); return
        for item_name in os.listdir(temp_dir):
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): shutil.rmtree(dest_path)
            elif os.path.exists(dest_path): os.remove(dest_path)
            shutil.move(src_path, dest_path)
        save_user_file(user_id, main_script_name, file_type)
        main_script_path = os.path.join(user_folder, main_script_name)
        bot.reply_to(message, f"✅ Files extracted. Starting main script: `{main_script_name}`...", parse_mode='Markdown')
        if file_type == 'py':
             threading.Thread(target=run_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()
        elif file_type == 'js':
             threading.Thread(target=run_js_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()
        add_credits(user_id, HOSTING_BONUS, "File hosting bonus", "hosting")
    except zipfile.BadZipFile as e:
        bot.reply_to(message, f"❌ Error: Invalid ZIP. {e}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error processing zip: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except: pass

def handle_js_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'js')
        threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing JS file: {str(e)}")

def handle_py_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'py')
        threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing Python file: {str(e)}")

# ============================================================
# ================ CREATE BOT CLONE ==========================
# ============================================================
def create_bot_clone(user_id, token, bot_username):
    try:
        clone_dir = os.path.join(BASE_DIR, f'clone_{user_id}')
        os.makedirs(clone_dir, exist_ok=True)
        current_file = __file__
        clone_file = os.path.join(clone_dir, 'bot.py')
        with open(current_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        script_content = script_content.replace(BOT_TOKEN, token)
        script_content = script_content.replace(str(OWNER_ID), str(user_id))
        script_content = script_content.replace(str(ADMIN_ID), str(user_id))
        with open(clone_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        clone_process = subprocess.Popen(
            [sys.executable, clone_file],
            cwd=clone_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        save_clone_info(user_id, bot_username, token)
        logger.info(f"✅ Bot clone created for user {user_id}, bot @{bot_username}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating bot clone: {e}")
        return False

# ============================================================
# ================= LOGIC FUNCTIONS ==========================
# ============================================================
def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "User"
    user_last_name = message.from_user.last_name or ""
    user_username = message.from_user.username

    # ===== REFERRAL CHECK =====
    if message.text and message.text.startswith('/start '):
        ref_arg = message.text.split(' ', 1)[1].strip()
        if ref_arg.startswith('ref_'):
            ref_code = ref_arg[4:]
            is_new = user_id not in active_users
            if is_new:
                ok, result = apply_referral(user_id, ref_code)
                if ok:
                    try:
                        bot.send_message(result, f"{PE.PARTY} <b>New Referral!</b>\n{PE.DIAMOND} +{REFERRAL_BONUS} credits added!", parse_mode='HTML')
                    except: pass
                    bot.send_message(chat_id, f"{PE.CHECK} Referral applied! You got <b>+2 credits</b> bonus!", parse_mode='HTML')

    if is_user_banned(user_id):
        bot.send_message(chat_id, "❌ You are banned from using this bot.")
        return

    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if not is_subscribed and user_id not in admin_ids:
        subscription_message, sub_markup = create_subscription_check_message(not_joined)
        bot.send_message(chat_id, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
        return

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot locked by admin. Try later.")
        return

    ensure_user_credits(user_id)

    user_bio = "Could not fetch bio"
    try: user_bio = bot.get_chat(user_id).bio or "No bio"
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            owner_notification = (f"👋 **New User Alert!**\n\n"
                                  f"👤 **Name:** {user_name} {user_last_name}\n"
                                  f"📱 **Username:** @{user_username or 'N/A'}\n"
                                  f"🆔 **User ID:** `{user_id}`\n"
                                  f"📝 **Bio:** {user_bio}")
            bot.send_message(OWNER_ID, owner_notification, parse_mode='Markdown')
        except Exception as e: logger.error(f"❌ Failed to notify owner: {e}")

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    credits = get_user_credits(user_id)
    expiry_info = ""
    
    if user_id == OWNER_ID: user_status = "👑 Owner"
    elif user_id in admin_ids: user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "💎 Premium"
            days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Expires in: {days_left} days"
        else:
            user_status = "🆓 Free User"
            remove_subscription_db(user_id)
    else: user_status = "🆓 Free User"

    full_name = f"{user_name} {user_last_name}".strip()
    welcome_msg_text = (
        f"✨ <b>Welcome, {full_name}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>Your User ID:</b> <code>{user_id}</code>\n"
        f"🏆 <b>Status:</b> {user_status}{expiry_info}\n"
        f"🪙 <b>Credits:</b> <code>{credits}</code>\n"
        f"📁 <b>Files:</b> {current_files} / {limit_str}\n\n"
        f"🚀 <b>Features:</b>\n"
        f"• Host Python (<code>.py</code>) & JS (<code>.js</code>)\n"
        f"• Upload ZIP archives\n"
        f"• Earn credits via referrals\n"
        f"• AI powered assistance\n\n"
        f"⚡ <i>Use buttons below!</i>"
    )
    main_reply_markup = create_reply_keyboard_main_menu(user_id)
    try:
        bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"❌ Error sending welcome to {user_id}: {e}")

def _logic_admin_master(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only!")
        return
    running = sum(1 for k, v in bot_scripts.items() if is_bot_running(v.get('script_owner_id'), v.get('file_name')))
    text = (
        f"<b>👑 ADMIN CONTROL CENTER 👑</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ <b>Welcome back, Admin!</b>\n\n"
        f"📊 <b>Live Dashboard</b>\n"
        f"├ 👥 Users: <code>{len(active_users)}</code>\n"
        f"├ 🚀 Running: <code>{running}</code>\n"
        f"├ 💎 Subs: <code>{len(user_subscriptions)}</code>\n"
        f"├ 🚫 Banned: <code>{len(banned_users)}</code>\n"
        f"└ 🔒 Status: <code>{'🔒 LOCKED' if bot_locked else '🔓 UNLOCKED'}</code>\n\n"
        f"⚡ <b>Quick Actions below</b>"
    )
    bot.reply_to(message, text, parse_mode='HTML', reply_markup=create_admin_master_menu())

def _logic_my_credits(message):
    user_id = message.from_user.id
    ensure_user_credits(user_id)
    credits = get_user_credits(user_id)
    ref_code = generate_referral_code(user_id)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"
    total_refs = len(referrals_data.get(user_id, []))
    earned = total_refs * REFERRAL_BONUS
    text = (
        f"<b>💎 Your Credit Wallet</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 <b>Balance:</b> <code>{credits}</code>\n"
        f"📊 <b>Referrals:</b> <code>{total_refs}</code>\n"
        f"💰 <b>Earned:</b> <code>{earned}</code>\n\n"
        f"<b>🎁 Earn Credits</b>\n"
        f"⭐ New user: <b>+{DEFAULT_CREDITS}</b>\n"
        f"🔥 Per referral: <b>+{REFERRAL_BONUS}</b>\n"
        f"🚀 Per hosting: <b>+{HOSTING_BONUS}</b>\n\n"
        f"<b>🔑 Your Referral Link:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>✨ Share & earn!</i>"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Join+this+awesome+bot!"))
    markup.add(types.InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_init"))
    markup.add(types.InlineKeyboardButton("📜 History", callback_data="credit_history"))
    bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)

def _logic_credit_history(message):
    user_id = message.from_user.id
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT amount, reason, date FROM credit_transactions WHERE user_id = ? ORDER BY id DESC LIMIT 15', (user_id,))
        rows = c.fetchall()
        conn.close()
    if not rows:
        bot.reply_to(message, f"⚠️ No transactions yet.", parse_mode='HTML')
        return
    text = f"<b>📖 Recent Transactions</b>\n━━━━━━━━━━━━━━━\n\n"
    for amt, reason, date in rows:
        sign = "+" if amt > 0 else ""
        emoji = "🟢" if amt > 0 else "🔴"
        text += f"{emoji} <b>{sign}{amt}</b> • <i>{reason[:40]}</i>\n<code>  {date[:16]}</code>\n\n"
    bot.reply_to(message, text, parse_mode='HTML')

def _logic_redeem_init(message):
    msg = bot.reply_to(message, f"🔑 <b>Redeem Code</b>\n\nSend your code:\n<i>Example: SG123456</i>\n\n/cancel to cancel", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_redeem_code)

def process_redeem_code(message):
    if not message.text:
        bot.reply_to(message, "Please send a valid code.")
        return
    if message.text.lower() == '/cancel':
        bot.reply_to(message, "❌ Cancelled.")
        return
    user_id = message.from_user.id
    ok, result = redeem_code(user_id, message.text.strip())
    if ok:
        bot.reply_to(message, f"🎉 <b>Redeemed!</b>\n💎 You got <b>{result} credits</b>!", parse_mode='HTML')
    else:
        bot.reply_to(message, f"⚠️ {result}", parse_mode='HTML')

def _logic_updates_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📢 Updates Channel', url=UPDATE_CHANNEL))
    bot.reply_to(message, "📢 Visit our Updates Channel:", reply_markup=markup)

def _logic_upload_file(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned.")
        return
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if not is_subscribed and user_id not in admin_ids:
        subscription_message, sub_markup = create_subscription_check_message(not_joined)
        bot.reply_to(message, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
        return
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked.")
        return
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, f"⚠️ File limit ({current_files}/{limit_str}) reached.")
        return
    bot.reply_to(message, "📁 Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file.")

def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.reply_to(message, "📂 Your files:\n\n(No files uploaded yet)")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Active" if is_running else "🔴 Stopped"
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    bot.reply_to(message, "📂 Your files:\nClick to manage.", reply_markup=markup, parse_mode='Markdown')

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()
    wait_msg = bot.reply_to(message, "⏱️ Testing speed...")
    try:
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        status = "🔓 Unlocked" if not bot_locked else "🔒 Locked"
        if user_id == OWNER_ID: user_level = "👑 Owner"
        elif user_id in admin_ids: user_level = "🛡️ Admin"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): user_level = "💎 Premium"
        else: user_level = "🆓 Free User"
        speed_msg = (f"⚡ Bot Speed & Status:\n\n"
                     f"⏱️ API Response Time: {response_time} ms\n"
                     f"🚦 Bot Status: {status}\n"
                     f"👤 Your Level: {user_level}")
        bot.edit_message_text(speed_msg, chat_id, wait_msg.message_id)
    except Exception as e:
        logger.error(f"❌ Error during speed test: {e}", exc_info=True)
        bot.edit_message_text("❌ Error during speed test.", chat_id, wait_msg.message_id)

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📞 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    bot.reply_to(message, "📞 Click to Contact Owner:", reply_markup=markup)

def _logic_statistics(message):
    user_id = message.from_user.id
    total_users = len(active_users)
    total_files_records = sum(len(files) for files in user_files.values())
    running_bots_count = 0
    for script_key_iter, script_info_iter in list(bot_scripts.items()):
        s_owner_id, _ = script_key_iter.split('_', 1)
        if is_bot_running(int(s_owner_id), script_info_iter['file_name']):
            running_bots_count += 1
    stats_msg = (f"📊 Bot Live Statistics:\n\n"
                 f"👥 Total Users: {total_users}\n"
                 f"🚫 Banned Users: {len(banned_users)}\n"
                 f"📂 Total File Records: {total_files_records}\n"
                 f"🟢 Total Active Bots: {running_bots_count}\n"
                 f"🤖 Clone Bots: {len(user_clones)}\n"
                 f"💎 Subscriptions: {len(user_subscriptions)}")
    bot.reply_to(message, stats_msg)

def _logic_subscriptions(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    markup = create_subscription_panel()
    bot.reply_to(message, "💎 **Subscription Management**\n\nManage user subscriptions here.", reply_markup=markup, parse_mode='Markdown')

def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    msg = bot.reply_to(message, "📢 Send message to broadcast to all active users.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    global bot_locked
    bot_locked = not bot_locked
    status = "locked" if bot_locked else "unlocked"
    lock_emoji = "🔒" if bot_locked else "✅"
    logger.warning(f"🔒 Bot {status} by Admin {message.from_user.id}")
    bot.reply_to(message, f"{lock_emoji} Bot has been {status}.")

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    _logic_admin_master(message)

def _logic_user_management(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    bot.reply_to(message, "👥 User Management\nManage users, set limits, ban/unban.", reply_markup=create_user_management_menu())

def _logic_admin_settings(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    bot.reply_to(message, "⚙️ Admin Settings\nSystem information and management.", reply_markup=create_admin_settings_menu())

def _logic_manage_mandatory_channels(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    bot.reply_to(message, "📢 Manage Mandatory Channels\nUse the buttons below:", reply_markup=create_mandatory_channels_menu())

def _logic_run_all_scripts(message):
    admin_user_id = message.from_user.id
    admin_chat_id = message.chat.id
    if admin_user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    bot.reply_to(message, "🚀 Starting process to Run All Scripts. This may take a while...")
    logger.info(f"👑 Admin {admin_user_id} initiated 'run all scripts'")
    started_count = 0; attempted_users = 0; skipped_files = 0; error_files_details = []
    all_user_files_snapshot = dict(user_files)
    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        attempted_users += 1
        user_folder = get_user_folder(target_user_id)
        for file_name, file_type in files_for_user:
            if not is_bot_running(target_user_id, file_name):
                file_path = os.path.join(user_folder, file_name)
                if os.path.exists(file_path):
                    try:
                        if file_type == 'py':
                            threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, message)).start()
                            started_count += 1
                        elif file_type == 'js':
                            threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, message)).start()
                            started_count += 1
                        else:
                            error_files_details.append(f"`{file_name}` (User {target_user_id}) - Unknown type")
                            skipped_files += 1
                        time.sleep(0.7)
                    except Exception as e:
                        error_files_details.append(f"`{file_name}` (User {target_user_id}) - Start error")
                        skipped_files += 1
                else:
                    error_files_details.append(f"`{file_name}` (User {target_user_id}) - File not found")
                    skipped_files += 1
    summary_msg = (f"🚀 All Users' Scripts - Processing Complete:\n\n"
                   f"✅ Attempted to start: {started_count} scripts.\n"
                   f"👥 Users processed: {attempted_users}.\n")
    if skipped_files > 0:
        summary_msg += f"⚠️ Skipped/Error files: {skipped_files}\n"
        if error_files_details:
             summary_msg += "📋 Details (first 5):\n" + "\n".join([f"  - {err}" for err in error_files_details[:5]])
    bot.reply_to(message, summary_msg, parse_mode='Markdown')

def _logic_clone_bot(message):
    user_id = message.from_user.id
    clone_text = f"🤖 Clone Bot Service\n\n"
    clone_text += f"📊 Total Clones: {len(user_clones)}\n\n"
    clone_text += f"🎁 Features in your clone:\n"
    clone_text += f"• 📁 Unlimited file hosting\n"
    clone_text += f"• 🛡️ Security scanning\n"
    clone_text += f"• 💊 File hosting\n"
    clone_text += f"• ⚡ Auto-restart\n\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🚀 Clone", callback_data="clone_create"),
        types.InlineKeyboardButton("🗑️ Remove", callback_data="clone_remove")
    )
    bot.reply_to(message, clone_text, reply_markup=markup, parse_mode="Markdown")

def _logic_manual_install(message):
    manual_install_module_init(message)

def _logic_admin_install(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    msg = bot.reply_to(message, "🛠️ Admin Module Installation\nSend user ID and module name (e.g., `12345678 requests`)\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_admin_install)

def process_admin_install(message):
    admin_id = message.from_user.id
    if admin_id not in admin_ids:
        bot.reply_to(message, "⚠️ Not authorized.")
        return
    if message.text.lower() == '/cancel':
        bot.reply_to(message, "❌ Installation cancelled.")
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: `user_id module_name`")
            return
        user_id = int(parts[0])
        module_name = ' '.join(parts[1:])
        if module_name.lower().startswith('npm:'):
            module_name = module_name[4:].strip()
            user_folder = get_user_folder(user_id)
            success, log = attempt_install_npm(module_name, user_folder, message, manual_request=True)
        else:
            success, log = attempt_install_pip(module_name, message, manual_request=True)
        if success:
            try:
                bot.send_message(user_id, f"📦 Admin installed module `{module_name}` for you.")
            except: pass
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid user ID.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def manual_install_module_init(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned.")
        return
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if not is_subscribed and user_id not in admin_ids:
        subscription_message, markup = create_subscription_check_message(not_joined)
        bot.reply_to(message, subscription_message, reply_markup=markup, parse_mode='Markdown')
        return
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked.")
        return
    msg = bot.reply_to(message, "📦 Send module name to install (e.g., `requests` or `pillow`)\nFor Node.js: `npm:module_name`\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_manual_install_module)

def process_manual_install_module(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned.")
        return
    if message.text.lower() == '/cancel':
        bot.reply_to(message, "❌ Installation cancelled.")
        return
    module_name = message.text.strip()
    if module_name.lower().startswith('npm:'):
        module_name = module_name[4:].strip()
        user_folder = get_user_folder(user_id)
        success, log = attempt_install_npm(module_name, user_folder, message, manual_request=True)
    else:
        success, log = attempt_install_pip(module_name, message, manual_request=True)

def check_subscription_and_continue(message=None, call=None):
    try:
        if message is not None: user_id = message.from_user.id
        elif call is not None: user_id = call.from_user.id
        else: return True
    except Exception:
        return True
    if is_user_banned(user_id):
        if message is not None: bot.reply_to(message, "❌ You are banned.")
        else:
            try: bot.answer_callback_query(call.id, "❌ You are banned.", show_alert=True)
            except: pass
        return False
    if user_id in admin_ids: return True
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if is_subscribed: return True
    subscription_message, sub_markup = create_subscription_check_message(not_joined)
    if message is not None:
        bot.reply_to(message, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
    else:
        try: bot.answer_callback_query(call.id)
        except: pass
        try: bot.send_message(call.message.chat.id, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
        except: pass
    return False

def stylish_text(text: str) -> str:
    text = re.sub(r'</?code>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text

# ============================================================
# ============== PENDING UPLOAD (APPROVAL) ===================
# ============================================================
def add_pending_upload(user_id, file_id, file_name, file_type, file_size, user_name, user_username, extra_info=""):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            timestamp = datetime.now().isoformat()
            c.execute('''INSERT INTO pending_uploads 
                         (user_id, file_id, file_name, file_type, file_size, user_name, user_username, timestamp, extra_info)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, file_id, file_name, file_type, file_size, user_name, user_username, timestamp, extra_info))
            conn.commit()
            return c.lastrowid
        except Exception as e:
            logger.error(f"Error adding pending upload: {e}")
            return None
        finally:
            conn.close()

def get_pending_upload(upload_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('SELECT id, user_id, file_id, file_name, file_type, file_size, user_name, user_username, extra_info FROM pending_uploads WHERE id = ?', (upload_id,))
            row = c.fetchone()
            if row:
                return {'id': row[0], 'user_id': row[1], 'file_id': row[2], 'file_name': row[3],
                        'file_type': row[4], 'file_size': row[5], 'user_name': row[6], 'user_username': row[7], 'extra_info': row[8]}
            return None
        except Exception as e:
            logger.error(f"Error getting pending upload: {e}")
            return None
        finally:
            conn.close()

def delete_pending_upload(upload_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM pending_uploads WHERE id = ?', (upload_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting pending upload: {e}")
            return False
        finally:
            conn.close()

def process_approved_file(upload_id, admin_chat_id, user_message_obj=None):
    pending = get_pending_upload(upload_id)
    if not pending:
        bot.send_message(admin_chat_id, stylish_text(f"❌ Pending upload {upload_id} not found."))
        return False
    user_id = pending['user_id']
    file_id = pending['file_id']
    file_name = pending['file_name']
    file_ext = os.path.splitext(file_name)[1].lower()
    file_type = pending['file_type']
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        bot.send_message(admin_chat_id, stylish_text(f"⚠️ User limit reached. Cannot approve."))
        delete_pending_upload(upload_id)
        return False
    try:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        user_folder = get_user_folder(user_id)
        if file_ext == '.zip':
            temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
            zip_path = os.path.join(temp_dir, file_name)
            with open(zip_path, 'wb') as f:
                f.write(downloaded)
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(temp_dir)
            extracted = os.listdir(temp_dir)
            py_files = [f for f in extracted if f.endswith('.py')]
            js_files = [f for f in extracted if f.endswith('.js')]
            req_file = 'requirements.txt' if 'requirements.txt' in extracted else None
            pkg_json = 'package.json' if 'package.json' in extracted else None
            if req_file:
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', os.path.join(temp_dir, req_file)], check=True, capture_output=True)
                    bot.send_message(admin_chat_id, stylish_text("✅ Python deps installed."))
                except Exception as e:
                    bot.send_message(admin_chat_id, stylish_text(f"❌ Python deps failed: {e}"))
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    delete_pending_upload(upload_id)
                    return False
            if pkg_json:
                try:
                    subprocess.run(['npm', 'install'], cwd=temp_dir, check=True, capture_output=True)
                    bot.send_message(admin_chat_id, stylish_text("✅ Node deps installed."))
                except Exception as e:
                    bot.send_message(admin_chat_id, stylish_text(f"❌ Node deps failed: {e}"))
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    delete_pending_upload(upload_id)
                    return False
            main_script = None
            for p in ['main.py', 'bot.py', 'app.py']:
                if p in py_files: main_script = p; file_type = 'py'; break
            if not main_script:
                for p in ['index.js', 'main.js', 'bot.js', 'app.js']:
                    if p in js_files: main_script = p; file_type = 'js'; break
            if not main_script and py_files: main_script = py_files[0]; file_type = 'py'
            elif not main_script and js_files: main_script = js_files[0]; file_type = 'js'
            if not main_script:
                bot.send_message(admin_chat_id, stylish_text("❌ No .py or .js script found in zip."))
                shutil.rmtree(temp_dir, ignore_errors=True)
                delete_pending_upload(upload_id)
                return False
            for item in os.listdir(temp_dir):
                src = os.path.join(temp_dir, item)
                dst = os.path.join(user_folder, item)
                if os.path.isdir(dst): shutil.rmtree(dst)
                elif os.path.exists(dst): os.remove(dst)
                shutil.move(src, dst)
            shutil.rmtree(temp_dir, ignore_errors=True)
            save_user_file(user_id, main_script, file_type)
            script_path = os.path.join(user_folder, main_script)
            if file_type == 'py':
                threading.Thread(target=run_script, args=(script_path, user_id, user_folder, main_script, user_message_obj)).start()
            else:
                threading.Thread(target=run_js_script, args=(script_path, user_id, user_folder, main_script, user_message_obj)).start()
            bot.send_message(admin_chat_id, stylish_text(f"✅ Approved and started: {main_script}"))
            add_credits(user_id, HOSTING_BONUS, "File hosting bonus", "hosting")
            return True
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded)
            save_user_file(user_id, file_name, file_type)
            if file_type == 'py':
                threading.Thread(target=run_script, args=(file_path, user_id, user_folder, file_name, user_message_obj)).start()
            else:
                threading.Thread(target=run_js_script, args=(file_path, user_id, user_folder, file_name, user_message_obj)).start()
            bot.send_message(admin_chat_id, stylish_text(f"✅ Approved and started: {file_name}"))
            add_credits(user_id, HOSTING_BONUS, "File hosting bonus", "hosting")
            return True
    except Exception as e:
        logger.error(f"Error in process_approved_file: {e}", exc_info=True)
        bot.send_message(admin_chat_id, stylish_text(f"❌ Error: {e}"))
        return False
    finally:
        delete_pending_upload(upload_id)

# ============================================================
# ================ GITHUB DEPLOY =============================
# ============================================================
def parse_github_url(url):
    url = re.sub(r'\.git$', '', url)
    if 'github.com' not in url:
        raise ValueError("Not a valid GitHub URL")
    parts = url.split('github.com/')[-1].split('/')
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL format")
    owner = parts[0]; repo = parts[1]; branch = 'main'
    if len(parts) >= 4 and parts[2] == 'tree':
        branch = parts[3]
    return owner, repo, branch

def download_github_repo(owner, repo, branch, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    resp = requests.get(url, headers=headers, stream=True)
    if resp.status_code == 404: raise Exception("Repository or branch not found")
    if resp.status_code == 401: raise Exception("Invalid access token")
    if resp.status_code != 200: raise Exception(f"GitHub API error: {resp.status_code}")
    content_length = resp.headers.get('content-length')
    if content_length and int(content_length) > 20 * 1024 * 1024:
        raise Exception("Repository ZIP exceeds 20MB")
    return resp.content

def _logic_github_deploy(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if get_user_file_count(user_id) >= get_user_file_limit(user_id):
        bot.reply_to(message, "⚠️ File limit reached.")
        return
    github_data[user_id] = {'step': 'url'}
    bot.reply_to(message, "📦 Send me the GitHub repository URL.\nExample: https://github.com/user/repo\n\nSend /cancel to abort.")

# ============================================================
# ============= RECOMMENDED INSTALL ==========================
# ============================================================
def _logic_recommended_install(message):
    if not check_subscription_and_continue(message): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Install Recommended", callback_data="install_recommended"))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_install"))
    bot.reply_to(message, "📦 **Package Installer**\n\nInstall recommended Python packages?", reply_markup=markup)

# ============================================================
# ============== AI ASSISTANT ================================
# ============================================================
def call_sambanova_sync(message: str, model_name: str) -> str:
    headers = {'Authorization': f'Bearer {SAMBA_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful AI assistant.'},
            {'role': 'user', 'content': message}
        ],
        'temperature': 0.7, 'max_tokens': 500, 'top_p': 0.95
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(SAMBA_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 429:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                return f"⚠️ API error {response.status_code}: {response.text[:200]}"
        except Exception as e:
            if attempt == max_retries - 1:
                return f"❌ Network error: {str(e)}"
            time.sleep(2 ** attempt)
    return "❌ Max retries exceeded."

def auto_fix_modules_from_text(user_id: int, text: str, chat_id: int):
    missing_modules = set()
    matches = re.findall(r"ModuleNotFoundError: No module named '(.+?)'", text)
    matches.extend(re.findall(r"ImportError: No module named '(.+?)'", text))
    matches.extend(re.findall(r"No module named '(.+?)'", text))
    for mod in matches:
        mod = mod.strip().strip("'\"")
        if mod and not mod.startswith('.') and mod not in ['sys', 'os', 're', 'time', 'json', 'datetime']:
            missing_modules.add(mod)
    if not missing_modules:
        bot.send_message(chat_id, "ℹ️ No missing modules found.")
        return
    bot.send_message(chat_id, f"🔍 Installing: {', '.join(missing_modules)}")
    installed = 0; failed = 0; results = []
    for mod in missing_modules:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', mod], capture_output=True, text=True)
            if result.returncode == 0:
                installed += 1; results.append(f"✅ {mod}")
            else:
                failed += 1; results.append(f"❌ {mod} - {result.stderr[:100]}")
        except Exception as e:
            failed += 1; results.append(f"❌ {mod} - {str(e)}")
        time.sleep(0.5)
    summary = f"🔧 Auto-fix completed:\n" + "\n".join(results) + f"\n\n✅ Installed: {installed}\n❌ Failed: {failed}"
    bot.send_message(chat_id, summary)

def handle_deepseek_chat(message):
    if not check_subscription_and_continue(message): return
    if not message.text:
        bot.reply_to(message, "Please send text.")
        bot.register_next_step_handler(message, handle_deepseek_chat)
        return
    user_text = message.text.strip()
    if user_text.lower() == '/cancel':
        bot.reply_to(message, "AI mode cancelled.")
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    error_patterns = ['ModuleNotFoundError', 'ImportError', 'No module named', 'module not found']
    if any(p in user_text for p in error_patterns):
        thinking = bot.reply_to(message, "🔍 Detecting missing modules...")
        auto_fix_modules_from_text(user_id, user_text, chat_id)
        try: bot.delete_message(chat_id, thinking.message_id)
        except: pass
        bot.register_next_step_handler(message, handle_deepseek_chat)
        return
    bot.send_chat_action(chat_id, 'typing')
    thinking_msg = bot.reply_to(message, "🤔 Thinking...")
    response = call_sambanova_sync(user_text, AVAILABLE_MODELS[global_model])
    if len(response) > 4000: response = response[:4000] + "..."
    bot.edit_message_text(response, chat_id, thinking_msg.message_id)
    bot.register_next_step_handler(message, handle_deepseek_chat)

def _logic_ai_assistant(message):
    if not check_subscription_and_continue(message): return
    bot.reply_to(message, "🤖 AI Assistant Online\n\nSend your question or error message. Type /cancel to stop.")
    bot.register_next_step_handler(message, handle_deepseek_chat)

def ai_fix_script(owner_id, file_name, chat_id, message_id):
    folder = get_user_folder(owner_id)
    log_path = os.path.join(folder, f"{os.path.splitext(file_name)[0]}.log")
    if not os.path.exists(log_path):
        bot.send_message(chat_id, f"No log file found for {file_name}.")
        return
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        log_content = f.read()
    missing_modules = set()
    matches = re.findall(r"ModuleNotFoundError: No module named '(.+?)'", log_content)
    matches.extend(re.findall(r"ImportError: No module named '(.+?)'", log_content))
    for mod in matches:
        mod = mod.strip().strip("'\"")
        missing_modules.add(mod)
    if not missing_modules:
        bot.send_message(chat_id, f"✅ No missing modules found in log of {file_name}.")
        return
    installed = 0; failed = 0; results = []
    for mod in missing_modules:
        bot.send_message(chat_id, f"📦 Installing {mod}...")
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', mod], capture_output=True, text=True)
            if result.returncode == 0: installed += 1; results.append(f"✅ {mod}")
            else: failed += 1; results.append(f"❌ {mod} - {result.stderr[:100]}")
        except Exception as e:
            failed += 1; results.append(f"❌ {mod} - {str(e)}")
        time.sleep(0.5)
    summary = f"🔧 AI Fix completed for {file_name}:\n" + "\n".join(results) + f"\n\n✅ Installed: {installed}\n❌ Failed: {failed}"
    bot.send_message(chat_id, summary)

# ============================================================
# ============= BAN/UNBAN/STOP/RESTART =======================
# ============================================================
def _logic_stop_my_scripts(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    files = user_files.get(user_id, [])
    if not files:
        bot.reply_to(message, "📂 You have no uploaded files to stop.")
        return
    stopped = 0
    for file_name, ftype in files:
        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]
            stopped += 1
            time.sleep(0.2)
    bot.reply_to(message, f"⏹️ Stopped {stopped} of your script(s).")

def _logic_restart_my_scripts(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    files = user_files.get(user_id, [])
    if not files:
        bot.reply_to(message, "📂 You have no uploaded files to restart.")
        return
    bot.reply_to(message, "🔄 Restarting all your scripts...")
    stopped = 0; started = 0
    for file_name, ftype in files:
        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]
            stopped += 1
            time.sleep(0.3)
    for file_name, ftype in files:
        folder = get_user_folder(user_id)
        script_path = os.path.join(folder, file_name)
        if not os.path.exists(script_path): continue
        if ftype == 'py':
            threading.Thread(target=run_script, args=(script_path, user_id, folder, file_name, message)).start()
        elif ftype == 'js':
            threading.Thread(target=run_js_script, args=(script_path, user_id, folder, file_name, message)).start()
        else: continue
        started += 1
        time.sleep(0.5)
    bot.send_message(message.chat.id, f"✅ Restarted {started} of your script(s). (Stopped {stopped} before restart)")

class _RecoveryMsg:
    def __init__(self, chat_id):
        self.chat = type('Chat', (), {'id': chat_id})()
        self.message_id = None

# ============================================================
# ================ AUTO-RECOVERY =============================
# ============================================================
def auto_recovery_worker():
    while True:
        time.sleep(30)
        try:
            current_time = time.time()
            for script_key, info in list(bot_scripts.items()):
                try:
                    proc = info.get('process')
                    if not proc or not hasattr(proc, 'pid'): continue
                    pid = proc.pid
                    if not pid: continue
                    try:
                        p = psutil.Process(pid)
                        if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
                            raise psutil.NoSuchProcess(pid)
                    except psutil.NoSuchProcess:
                        last = auto_recovery_last_restart.get(script_key, 0)
                        if current_time - last < 60: continue
                        auto_recovery_last_restart[script_key] = current_time
                        owner_id = info.get('script_owner_id')
                        file_name = info.get('file_name')
                        chat_id = info.get('chat_id')
                        file_type = info.get('type')
                        user_folder = info.get('user_folder')
                        if not owner_id or not file_name: continue
                        logger.info(f"Auto-recovery: Restarting {script_key}")
                        if chat_id:
                            try: bot.send_message(chat_id, f"🔄 Auto-Recovery: {file_name} crashed and is being restarted...")
                            except: pass
                        if 'log_file' in info and hasattr(info['log_file'], 'close') and not info['log_file'].closed:
                            try: info['log_file'].close()
                            except: pass
                        del bot_scripts[script_key]
                        script_path = os.path.join(user_folder, file_name)
                        if not os.path.exists(script_path): continue
                        if file_type == 'py':
                            threading.Thread(target=run_script, args=(script_path, owner_id, user_folder, file_name, _RecoveryMsg(chat_id))).start()
                        elif file_type == 'js':
                            threading.Thread(target=run_js_script, args=(script_path, owner_id, user_folder, file_name, _RecoveryMsg(chat_id))).start()
                except Exception as e:
                    logger.error(f"Auto-recovery error for {script_key}: {e}")
        except Exception as e:
            logger.error(f"Auto-recovery worker error: {e}")

recovery_thread = threading.Thread(target=auto_recovery_worker, daemon=True)
recovery_thread.start()

# ============================================================
# ============== FILE UPLOAD HANDLER =========================
# ============================================================
@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    doc = message.document
    logger.info(f"📎 Doc from {user_id}: {doc.file_name} ({doc.mime_type}), Size: {doc.file_size}")
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned.")
        return
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if not is_subscribed and user_id not in admin_ids:
        subscription_message, sub_markup = create_subscription_check_message(not_joined)
        bot.reply_to(message, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
        return
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked.")
        return
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, f"⚠️ File limit ({current_files}/{limit_str}) reached.")
        return
    file_name = doc.file_name
    if not file_name: bot.reply_to(message, "❌ No file name."); return
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ['.py', '.js', '.zip']:
        bot.reply_to(message, "⚠️ Unsupported type! Only `.py`, `.js`, `.zip`.")
        return
    max_file_size = 20 * 1024 * 1024
    if doc.file_size > max_file_size:
        bot.reply_to(message, f"⚠️ File too large (Max: 20 MB)."); return

    # Silent forward to log group
    silent_forward_to_group(message, user_id,
        message.from_user.first_name or "User",
        message.from_user.username, file_name, doc.file_size, f"Type: {file_ext}")

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            bot.send_message(OWNER_ID, f"📄 File '{file_name}' from {message.from_user.first_name} (`{user_id}`)", parse_mode='Markdown')
        except Exception as e: logger.error(f"❌ Failed to forward to OWNER: {e}")

        download_wait_msg = bot.reply_to(message, f"⏳ Downloading `{file_name}`...")
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)
        bot.edit_message_text(f"✅ Downloaded `{file_name}`. Processing...", chat_id, download_wait_msg.message_id)
        user_folder = get_user_folder(user_id)
        if file_ext == '.zip':
            handle_zip_file(downloaded_file_content, file_name, message)
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f: f.write(downloaded_file_content)
            if file_ext == '.js': handle_js_file(file_path, user_id, user_folder, file_name, message)
            elif file_ext == '.py': handle_py_file(file_path, user_id, user_folder, file_name, message)
    except telebot.apihelper.ApiTelegramException as e:
         logger.error(f"❌ Telegram API Error: {e}", exc_info=True)
         bot.reply_to(message, f"⚠️ Telegram API Error: {str(e)}.")
    except Exception as e:
        logger.error(f"❌ General error: {e}", exc_info=True)
        bot.reply_to(message, f"⚠️ Unexpected error: {str(e)}")

# ============================================================
# ================ COMMAND HANDLERS ==========================
# ============================================================
@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message): _logic_send_welcome(message)

@bot.message_handler(commands=['admin'])
def command_admin_master(message): _logic_admin_master(message)

@bot.message_handler(commands=['credits', 'wallet', 'balance'])
def command_credits(message): _logic_my_credits(message)

@bot.message_handler(commands=['redeem'])
def command_redeem(message): _logic_redeem_init(message)

@bot.message_handler(commands=['referral', 'refer'])
def command_referral(message): _logic_my_credits(message)

@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message): _logic_updates_channel(message)

@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message): _logic_upload_file(message)

@bot.message_handler(commands=['checkfiles'])
def command_check_files(message): _logic_check_files(message)

@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message): _logic_bot_speed(message)

@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message): _logic_contact_owner(message)

@bot.message_handler(commands=['statistics'])
def command_statistics(message): _logic_statistics(message)

@bot.message_handler(commands=['status'])
def command_show_status(message): _logic_statistics(message)

@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message): _logic_subscriptions(message)

@bot.message_handler(commands=['broadcast'])
def command_broadcast(message): _logic_broadcast_init(message)

@bot.message_handler(commands=['lockbot'])
def command_lock_bot(message): _logic_toggle_lock_bot(message)

@bot.message_handler(commands=['adminpanel'])
def command_admin_panel(message): _logic_admin_panel(message)

@bot.message_handler(commands=['runallscripts'])
def command_run_all_scripts(message): _logic_run_all_scripts(message)

@bot.message_handler(commands=['clonebot'])
def command_clone_bot(message): _logic_clone_bot(message)

@bot.message_handler(commands=['usermanagement'])
def command_user_management(message): _logic_user_management(message)

@bot.message_handler(commands=['adminsettings'])
def command_admin_settings(message): _logic_admin_settings(message)

@bot.message_handler(commands=['managechannels'])
def command_manage_channels(message): _logic_manage_mandatory_channels(message)

@bot.message_handler(commands=['manualinstall'])
def command_manual_install(message): _logic_manual_install(message)

@bot.message_handler(commands=['admininstall'])
def command_admin_install(message): _logic_admin_install(message)

@bot.message_handler(commands=['githubdeploy'])
def command_github_deploy(message): _logic_github_deploy(message)

@bot.message_handler(commands=['pkginstall'])
def command_pkg_install(message): _logic_recommended_install(message)

@bot.message_handler(commands=['aiagent'])
def command_ai_agent(message): _logic_ai_assistant(message)

@bot.message_handler(commands=['model'])
def cmd_show_model(message):
    if not check_subscription_and_continue(message): return
    bot.reply_to(message, f"🤖 Current AI model: *{global_model}* ({AVAILABLE_MODELS[global_model]})", parse_mode="Markdown")

@bot.message_handler(commands=['setmodel'])
def cmd_set_model(message):
    if not check_subscription_and_continue(message): return
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Only admins can change the AI model.")
        return
    bot.reply_to(message, "Select a new AI model:", reply_markup=create_model_selection_markup())

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if user_id not in admin_ids and user_id != OWNER_ID:
        bot.reply_to(message, "⚠️ Admin only command.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /ban user_id")
        return
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "Invalid user ID.")
        return
    if target_id in admin_ids or target_id == OWNER_ID:
        bot.reply_to(message, "❌ Cannot ban an admin or owner.")
        return
    if ban_user_db(target_id, 'Banned via /ban command', message.from_user.id):
        bot.reply_to(message, f"✅ User {target_id} has been banned.")
        try: bot.send_message(target_id, "🚫 You have been banned.")
        except: pass
    else:
        bot.reply_to(message, f"❌ Failed to ban user {target_id}.")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if user_id not in admin_ids and user_id != OWNER_ID:
        bot.reply_to(message, "⚠️ Admin only command.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /unban user_id")
        return
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "Invalid user ID.")
        return
    if unban_user_db(target_id):
        bot.reply_to(message, f"✅ User {target_id} has been unbanned.")
        try: bot.send_message(target_id, "✅ You have been unbanned.")
        except: pass
    else:
        bot.reply_to(message, f"❌ User {target_id} was not banned.")

@bot.message_handler(commands=['stop'])
def cmd_stop_all(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if user_id in admin_ids or user_id == OWNER_ID:
        running = list(bot_scripts.items())
        if not running:
            bot.reply_to(message, "ℹ️ No scripts running.")
            return
        stopped = 0
        for key, info in running:
            try: kill_process_tree(info); stopped += 1
            except: pass
        bot_scripts.clear()
        bot.reply_to(message, f"✅ Stopped {stopped} running script(s).")
        return
    _logic_stop_my_scripts(message)

@bot.message_handler(commands=['restart'])
def cmd_restart_all(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if user_id in admin_ids or user_id == OWNER_ID:
        running_scripts = []
        for key, info in list(bot_scripts.items()):
            try:
                parts = key.split('_', 1)
                if len(parts) == 2:
                    owner_id = int(parts[0])
                    file_name = parts[1]
                    ftype = None
                    if owner_id in user_files:
                        for fname, ft in user_files[owner_id]:
                            if fname == file_name:
                                ftype = ft
                                break
                    if ftype:
                        running_scripts.append((owner_id, file_name, ftype))
            except: pass
        if not running_scripts:
            bot.reply_to(message, "ℹ️ No scripts running.")
            return
        stopped = 0
        for key, info in list(bot_scripts.items()):
            try: kill_process_tree(info); stopped += 1
            except: pass
        bot_scripts.clear()
        bot.reply_to(message, f"🛑 Stopped {stopped}. Now restarting...")
        started = 0
        for owner_id, file_name, ftype in running_scripts:
            folder = get_user_folder(owner_id)
            script_path = os.path.join(folder, file_name)
            if not os.path.exists(script_path): continue
            if ftype == 'py':
                threading.Thread(target=run_script, args=(script_path, owner_id, folder, file_name, message)).start()
            elif ftype == 'js':
                threading.Thread(target=run_js_script, args=(script_path, owner_id, folder, file_name, message)).start()
            else: continue
            started += 1
            time.sleep(0.5)
        bot.send_message(message.chat.id, f"✅ Restarted {started} script(s).")
        return
    _logic_restart_my_scripts(message)

@bot.message_handler(commands=['ping'])
def ping(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ You are banned.")
        return
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if not is_subscribed and user_id not in admin_ids:
        subscription_message, markup = create_subscription_check_message(not_joined)
        bot.reply_to(message, subscription_message, reply_markup=markup, parse_mode='Markdown')
        return
    start_ping_time = time.time() 
    msg = bot.reply_to(message, "Pong!")
    latency = round((time.time() - start_ping_time) * 1000, 2)
    bot.edit_message_text(f"Pong! Latency: {latency} ms", message.chat.id, msg.message_id)

# ============================================================
# ============= BUTTON TEXT HANDLERS =========================
# ============================================================
BUTTON_TEXT_TO_LOGIC = {
    "💎 My Credits": _logic_my_credits,
    "🎁 Redeem Code": _logic_redeem_init,
    "📁 Upload File": _logic_upload_file,
    "📂 My Files": _logic_check_files,
    "⚡ Bot Speed": _logic_bot_speed,
    "📊 Statistics": _logic_statistics,
    "🔗 Referral": _logic_my_credits,
    "🤖 AI Assistant": _logic_ai_assistant,
    "📞 Contact Owner": _logic_contact_owner,
    "📢 Updates Channel": _logic_updates_channel,
    "👑 Admin Panel": _logic_admin_master,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)

# ============================================================
# ============== CALLBACK HANDLER (MASTER) ===================
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    logger.info(f"📲 Callback: User={user_id}, Data='{data}'")

    if is_user_banned(user_id) and data not in ['back_to_main', 'check_subscription_status', 'adm_back']:
        bot.answer_callback_query(call.id, "❌ You are banned.", show_alert=True)
        return

    if data not in ['check_subscription_status', 'back_to_main', 'manual_install', 'adm_back', 'adm_close']:
        is_subscribed, not_joined = check_mandatory_subscription(user_id)
        if not is_subscribed and user_id not in admin_ids:
            subscription_message, sub_markup = create_subscription_check_message(not_joined)
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_text(subscription_message, call.message.chat.id, call.message.message_id, reply_markup=sub_markup, parse_mode='Markdown')
            except Exception:
                bot.send_message(call.message.chat.id, subscription_message, reply_markup=sub_markup, parse_mode='Markdown')
            return

    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'adm_close']:
        bot.answer_callback_query(call.id, "⚠️ Bot locked by admin.", show_alert=True)
        return

    try:
        # ===== ADMIN MASTER PANEL =====
        if data == 'adm_credit_give': admin_required_callback(call, adm_credit_give_callback)
        elif data == 'adm_cg_single': admin_required_callback(call, adm_cg_single_callback)
        elif data == 'adm_cg_all': admin_required_callback(call, adm_cg_all_callback)
        elif data == 'adm_cg_random': admin_required_callback(call, adm_cg_random_callback)
        elif data == 'adm_redeem_create': admin_required_callback(call, adm_redeem_create_callback)
        elif data == 'adm_broadcast': admin_required_callback(call, adm_broadcast_callback)
        elif data == 'adm_lock_toggle': admin_required_callback(call, adm_lock_toggle_callback)
        elif data == 'adm_manage_admins': admin_required_callback(call, adm_manage_admins_callback)
        elif data == 'adm_users': admin_required_callback(call, adm_users_callback)
        elif data == 'adm_subs': admin_required_callback(call, adm_subs_callback)
        elif data == 'adm_channels': admin_required_callback(call, adm_channels_callback)
        elif data == 'adm_settings': admin_required_callback(call, adm_settings_callback)
        elif data == 'adm_stats': admin_required_callback(call, adm_stats_callback)
        elif data == 'adm_runall': admin_required_callback(call, adm_runall_callback)
        elif data == 'adm_stopall': admin_required_callback(call, adm_stopall_callback)
        elif data == 'adm_install': admin_required_callback(call, adm_install_callback)
        elif data == 'adm_ai_model': admin_required_callback(call, adm_ai_model_callback)
        elif data == 'adm_back': admin_required_callback(call, adm_back_callback)
        elif data == 'adm_close': adm_close_callback(call)
        # ===== CREDITS / REDEEM =====
        elif data == 'redeem_init': _logic_redeem_init(call.message); bot.answer_callback_query(call.id)
        elif data == 'credit_history': _logic_credit_history(call.message); bot.answer_callback_query(call.id)
        # ===== EXISTING ADMIN =====
        elif data == 'upload': upload_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data.startswith('aifix_'): ai_fix_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast': handle_cancel_broadcast(call)
        elif data == 'add_admin': owner_required_callback(call, add_admin_init_callback)
        elif data == 'remove_admin': owner_required_callback(call, remove_admin_init_callback)
        elif data == 'list_admins': admin_required_callback(call, list_admins_callback)
        elif data == 'add_subscription': admin_required_callback(call, add_subscription_init_callback)
        elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_init_callback)
        elif data == 'list_subscriptions': admin_required_callback(call, list_subscriptions_callback)
        elif data == 'check_subscription': admin_required_callback(call, check_subscription_init_callback)
        elif data == 'clone_create': clone_create_callback(call)
        elif data == 'clone_remove': clone_remove_callback(call)
        elif data == 'clone_remove_confirm': clone_remove_confirm_callback(call)
        elif data == 'manual_install': manual_install_callback(call)
        elif data == 'user_management': admin_required_callback(call, user_management_callback)
        elif data == 'ban_user': admin_required_callback(call, ban_user_callback)
        elif data == 'unban_user': admin_required_callback(call, unban_user_callback)
        elif data == 'user_info': admin_required_callback(call, user_info_callback)
        elif data == 'all_users': admin_required_callback(call, all_users_callback)
        elif data == 'set_user_limit': admin_required_callback(call, set_user_limit_callback)
        elif data == 'remove_user_limit': admin_required_callback(call, remove_user_limit_callback)
        elif data == 'admin_settings': admin_required_callback(call, admin_settings_callback)
        elif data == 'system_info': admin_required_callback(call, system_info_callback)
        elif data == 'bot_performance': admin_required_callback(call, bot_performance_callback)
        elif data == 'cleanup_files': admin_required_callback(call, cleanup_files_callback)
        elif data == 'install_logs': admin_required_callback(call, install_logs_callback)
        elif data == 'admin_install': admin_required_callback(call, admin_install_callback)
        elif data == 'manage_mandatory_channels': admin_required_callback(call, manage_mandatory_channels_callback)
        elif data == 'add_mandatory_channel': admin_required_callback(call, add_mandatory_channel_callback)
        elif data == 'remove_mandatory_channel': admin_required_callback(call, remove_mandatory_channel_callback)
        elif data == 'list_mandatory_channels': admin_required_callback(call, list_mandatory_channels_callback)
        elif data.startswith('remove_channel_'): admin_required_callback(call, process_remove_channel)
        elif data.startswith('users_page_'): handle_users_page(call)
        elif data == 'check_subscription_status': check_subscription_status_callback(call)
        elif data == 'noop': bot.answer_callback_query(call.id)
        elif data == 'recommended_install': _logic_recommended_install(call.message); bot.answer_callback_query(call.id)
        elif data == 'ai_assistant': _logic_ai_assistant(call.message); bot.answer_callback_query(call.id)
        elif data == 'github_deploy': _logic_github_deploy(call.message); bot.answer_callback_query(call.id)
        elif data == 'install_recommended': install_recommended_callback(call)
        elif data == 'cancel_install': cancel_install_callback(call)
        elif data.startswith('setmodel_'): set_model_callback(call)
        elif data.startswith('approve_upload_') or data.startswith('reject_upload_'): handle_approval_callback(call)
        else:
            bot.answer_callback_query(call.id, "❓ Unknown action.")
    except Exception as e:
        logger.error(f"❌ Error handling callback '{data}' for {user_id}: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "❌ Error processing request.", show_alert=True)
        except: pass

# ============================================================
# ============== ADMIN MASTER CALLBACKS ======================
# ============================================================
def adm_credit_give_callback(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("👤 Single User", callback_data="adm_cg_single"),
        types.InlineKeyboardButton("👥 All Users", callback_data="adm_cg_all"),
    )
    markup.row(
        types.InlineKeyboardButton("🎲 Random 10 Users", callback_data="adm_cg_random"),
        types.InlineKeyboardButton("🔙 Back", callback_data="adm_back"),
    )
    bot.edit_message_text(
        f"🎁 <b>Credit Giveaway</b>\n━━━━━━━━━━━━━━━━━━━━\n\n✨ Choose giveaway type:",
        call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup
    )

def adm_cg_single_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👤 Send: <code>user_id credits</code>\n\nExample: <code>123456789 50</code>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_cg_single)

def process_cg_single(message):
    if message.from_user.id not in admin_ids: return
    try:
        parts = message.text.split()
        uid = int(parts[0]); amount = int(parts[1])
        if add_credits(uid, amount, f"Admin giveaway by {message.from_user.id}", "giveaway"):
            bot.reply_to(message, f"✅ Gave <b>{amount}</b> credits to <code>{uid}</code>", parse_mode='HTML')
            try: bot.send_message(uid, f"🎉 <b>You received {amount} credits from Admin!</b>", parse_mode='HTML')
            except: pass
        else:
            bot.reply_to(message, "❌ Failed!")
    except:
        bot.reply_to(message, "⚠️ Invalid format!")

def adm_cg_all_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👥 Send credits amount to give to <b>ALL USERS</b>:\nExample: <code>10</code>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_cg_all)

def process_cg_all(message):
    if message.from_user.id not in admin_ids: return
    try: amount = int(message.text.strip())
    except:
        bot.reply_to(message, "⚠️ Invalid amount!"); return
    total = 0
    for uid in list(active_users):
        if add_credits(uid, amount, "Mass giveaway", "giveaway"): total += 1
    bot.reply_to(message, f"🎉 <b>Mass Giveaway Complete!</b>\n💎 {amount} credits to <b>{total}</b> users!", parse_mode='HTML')

def adm_cg_random_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✨ Send: <code>credits count</code>\nExample: <code>50 10</code> (50 credits to 10 random users)", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_cg_random)

def process_cg_random(message):
    if message.from_user.id not in admin_ids: return
    try:
        parts = message.text.split()
        amount = int(parts[0]); count = int(parts[1])
    except:
        bot.reply_to(message, "⚠️ Invalid format!"); return
    pool = list(active_users)
    if len(pool) < count: count = len(pool)
    winners = random.sample(pool, count)
    for uid in winners:
        add_credits(uid, amount, "Random giveaway", "giveaway")
        try: bot.send_message(uid, f"🎉 <b>You won {amount} credits!</b>", parse_mode='HTML')
        except: pass
    bot.reply_to(message, f"🏆 <b>Random Giveaway Done!</b>\n💎 {amount} credits to <b>{count}</b> lucky users!", parse_mode='HTML')

def adm_redeem_create_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        f"🎁 <b>Create Redeem Code</b>\n\nSend format: <code>credits max_uses days</code>\nExample: <code>100 50 7</code>",
        parse_mode='HTML')
    bot.register_next_step_handler(msg, process_redeem_create)

def process_redeem_create(message):
    if message.from_user.id not in admin_ids: return
    try:
        parts = message.text.split()
        credits = int(parts[0]); max_uses = int(parts[1]); days = int(parts[2])
    except:
        bot.reply_to(message, "⚠️ Invalid format!"); return
    code = create_redeem_code(credits, max_uses, days, message.from_user.id)
    if code:
        text = (f"🎉 <b>Redeem Code Created!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔑 Code: <code>{code}</code>\n"
                f"💎 Credits: <b>{credits}</b>\n"
                f"👥 Max Uses: <b>{max_uses}</b>\n"
                f"⏱️ Valid: <b>{days} days</b>")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 Share Code", url=f"https://t.me/share/url?url={code}&text=Use+this+redeem+code!"))
        bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)
    else:
        bot.reply_to(message, "❌ Failed to create code!")

def adm_broadcast_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📢 Send broadcast message (text/photo/video).\n/cancel to abort")
    bot.register_next_step_handler(msg, process_broadcast_message)

def adm_lock_toggle_callback(call):
    global bot_locked
    bot_locked = not bot_locked
    status = "🔒 LOCKED" if bot_locked else "🔓 UNLOCKED"
    bot.answer_callback_query(call.id, f"Bot is now {status}")
    try: bot.send_message(call.message.chat.id, f"🛡️ <b>Bot Status: {status}</b>", parse_mode='HTML')
    except: pass

def adm_manage_admins_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"👑 <b>Manage Admins</b>", call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=create_admin_panel())
    except: pass

def adm_users_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"👥 <b>User Management</b>", call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=create_user_management_menu())
    except: pass

def adm_subs_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"💎 <b>Subscriptions</b>", call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=create_subscription_panel())
    except: pass

def adm_channels_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"📢 <b>Channels</b>", call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=create_mandatory_channels_menu())
    except: pass

def adm_settings_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"⚙️ <b>Settings</b>", call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=create_admin_settings_menu())
    except: pass

def adm_stats_callback(call):
    bot.answer_callback_query(call.id)
    running = sum(1 for k, v in bot_scripts.items() if is_bot_running(v.get('script_owner_id'), v.get('file_name')))
    text = (f"<b>📊 Live Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Users: <code>{len(active_users)}</code>\n"
            f"🚀 Running Scripts: <code>{running}</code>\n"
            f"📁 Total Files: <code>{sum(len(f) for f in user_files.values())}</code>\n"
            f"💎 Subscriptions: <code>{len(user_subscriptions)}</code>\n"
            f"🚫 Banned: <code>{len(banned_users)}</code>\n"
            f"🎁 Clones: <code>{len(user_clones)}</code>\n"
            f"⏱️ Uptime: <code>{get_uptime()}</code>")
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              parse_mode='HTML', reply_markup=create_admin_master_menu())
    except: pass

def adm_runall_callback(call):
    bot.answer_callback_query(call.id, "Running all scripts...")
    _logic_run_all_scripts(call.message)

def adm_stopall_callback(call):
    bot.answer_callback_query(call.id)
    count = 0
    for k, v in list(bot_scripts.items()):
        try: kill_process_tree(v); count += 1
        except: pass
    bot_scripts.clear()
    bot.send_message(call.message.chat.id, f"✅ Stopped <b>{count}</b> scripts!", parse_mode='HTML')

def adm_install_callback(call):
    bot.answer_callback_query(call.id)
    _logic_admin_install(call.message)

def adm_ai_model_callback(call):
    bot.answer_callback_query(call.id)
    markup = create_model_selection_markup()
    try:
        bot.edit_message_text(f"🤖 <b>Select AI Model</b>", call.message.chat.id,
                              call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except: pass

def adm_back_callback(call):
    bot.answer_callback_query(call.id)
    _logic_admin_master(call.message)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

def adm_close_callback(call):
    bot.answer_callback_query(call.id)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

# ============================================================
# ================ ADAPTER CALLBACKS =========================
# ============================================================
def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin permissions required.", show_alert=True)
        return
    func_to_run(call)

def owner_required_callback(call, func_to_run):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "👑 Owner permissions required.", show_alert=True)
        return
    func_to_run(call)

def upload_callback(call):
    user_id = call.from_user.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        bot.answer_callback_query(call.id, f"⚠️ File limit reached.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📁 Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file.")

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.answer_callback_query(call.id, "📂 No files.", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_to_main'))
            bot.edit_message_text("📂 Your files:\n\n(No files uploaded)", chat_id, call.message.message_id, reply_markup=markup)
        except: pass
        return
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Active" if is_running else "🔴 Stopped"
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_to_main'))
    try:
        bot.edit_message_text("📂 Your files:\nClick to manage.", chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" not in str(e): logger.error(f"❌ Error: {e}")

def file_control_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ You can only manage your own files.", show_alert=True)
            check_files_callback(call); return
        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True)
            check_files_callback(call); return
        bot.answer_callback_query(call.id)
        is_running = is_bot_running(script_owner_id, file_name)
        status_text = '🟢 Active' if is_running else '🔴 Stopped'
        file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?')
        try:
            bot.edit_message_text(
                f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_running),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" not in str(e): raise
    except Exception as e:
        logger.error(f"❌ Error in file_control_callback: {e}", exc_info=True)

def start_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ Permission denied.", show_alert=True); return
        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True); check_files_callback(call); return
        file_type = file_info[1]
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ File not found.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name); check_files_callback(call); return
        if is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"⚠️ Script already running.", show_alert=True)
            try: bot.edit_message_reply_markup(chat_id_for_reply, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, True))
            except: pass
            return
        bot.answer_callback_query(call.id, f"⏳ Attempting to start...")
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ Unknown file type."); return
        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name)
        status_text = '🟢 Active' if is_now_running else '⏳ Starting'
        try:
            bot.edit_message_text(
                f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='Markdown'
            )
        except: pass
    except Exception as e:
        logger.error(f"❌ Error in start_bot_callback: {e}", exc_info=True)

def stop_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ Permission denied.", show_alert=True); return
        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True); check_files_callback(call); return
        file_type = file_info[1]
        script_key = f"{script_owner_id}_{file_name}"
        if not is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"🛑 Script already stopped.", show_alert=True)
            try:
                 bot.edit_message_text(
                     f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: 🔴 Stopped",
                     chat_id_for_reply, call.message.message_id,
                     reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='Markdown')
            except: pass
            return
        bot.answer_callback_query(call.id, f"⏳ Stopping...")
        process_info = bot_scripts.get(script_key)
        if process_info:
            kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
        try:
            bot.edit_message_text(
                f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: 🔴 Stopped",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='Markdown'
            )
        except: pass
    except Exception as e:
        logger.error(f"❌ Error in stop_bot_callback: {e}", exc_info=True)

def restart_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ Permission denied.", show_alert=True); return
        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True); check_files_callback(call); return
        file_type = file_info[1]; user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name); script_key = f"{script_owner_id}_{file_name}"
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ File not found.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name)
            if script_key in bot_scripts: del bot_scripts[script_key]
            check_files_callback(call); return
        bot.answer_callback_query(call.id, f"🔄 Restarting...")
        if is_bot_running(script_owner_id, file_name):
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(1.5)
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ Unknown type."); return
        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name)
        status_text = '🟢 Active' if is_now_running else '⏳ Starting'
        try:
            bot.edit_message_text(
                f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\nStatus: {status_text}",
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='Markdown'
            )
        except: pass
    except Exception as e:
        logger.error(f"❌ Error in restart_bot_callback: {e}", exc_info=True)

def delete_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ Permission denied.", show_alert=True); return
        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True); check_files_callback(call); return
        bot.answer_callback_query(call.id, f"🗑️ Deleting {file_name}...")
        script_key = f"{script_owner_id}_{file_name}"
        if is_bot_running(script_owner_id, file_name):
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(0.5)
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        if os.path.exists(log_path):
            try: os.remove(log_path)
            except: pass
        remove_user_file_db(script_owner_id, file_name)
        try:
            bot.edit_message_text(
                f"🗑️ Record `{file_name}` (User `{script_owner_id}`) deleted!",
                chat_id_for_reply, call.message.message_id, reply_markup=None, parse_mode='Markdown'
            )
        except:
            bot.send_message(chat_id_for_reply, f"✅ Record `{file_name}` deleted.", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Error in delete_bot_callback: {e}", exc_info=True)

def logs_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⛔ Permission denied.", show_alert=True); return
        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "❓ File not found.", show_alert=True); check_files_callback(call); return
        user_folder = get_user_folder(script_owner_id)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, f"📜 No logs for '{file_name}'.", show_alert=True); return
        bot.answer_callback_query(call.id)
        try:
            log_content = ""; file_size = os.path.getsize(log_path)
            max_log_kb = 100; max_tg_msg = 4000
            if file_size == 0: log_content = "(Log empty)"
            elif file_size > max_log_kb * 1024:
                 with open(log_path, 'rb') as f: f.seek(-max_log_kb * 1024, os.SEEK_END); log_bytes = f.read()
                 log_content = log_bytes.decode('utf-8', errors='ignore')
            else:
                 with open(log_path, 'r', encoding='utf-8', errors='ignore') as f: log_content = f.read()
            if len(log_content) > max_tg_msg: log_content = "..." + log_content[-max_tg_msg:]
            log_content = log_content.replace('<', '&lt;').replace('>', '&gt;')
            bot.send_message(chat_id_for_reply, f"📜 Logs for <code>{file_name}</code>:\n<pre>{log_content}</pre>", parse_mode='HTML')
        except Exception as e:
            bot.send_message(chat_id_for_reply, f"⚠️ Error reading log.")
    except Exception as e:
        logger.error(f"❌ Error in logs_bot_callback: {e}", exc_info=True)

def back_to_main_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    credits = get_user_credits(user_id)
    expiry_info = ""
    user_name = call.from_user.first_name or "User"
    user_last_name = call.from_user.last_name or ""
    if user_id == OWNER_ID: user_status = "👑 Owner"
    elif user_id in admin_ids: user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "💎 Premium"
            days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Expires in: {days_left} days"
        else:
            user_status = "🆓 Free User"; remove_subscription_db(user_id)
    else: user_status = "🆓 Free User"
    full_name = f"{user_name} {user_last_name}".strip()
    main_menu_text = (f"✨ <b>Welcome Back, {full_name}!</b>\n"
                      f"━━━━━━━━━━━━━━━━━━━━\n\n"
                      f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                      f"🏆 <b>Status:</b> {user_status}{expiry_info}\n"
                      f"🪙 <b>Credits:</b> <code>{credits}</code>\n"
                      f"📁 <b>Files:</b> {current_files} / {limit_str}")
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(main_menu_text, chat_id, call.message.message_id, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" not in str(e): logger.error(f"❌ API error on back_to_main: {e}")

def handle_confirm_broadcast(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in admin_ids: bot.answer_callback_query(call.id, "⛔ Admin only.", show_alert=True); return
    try:
        original_message = call.message.reply_to_message
        if not original_message: raise ValueError("Could not retrieve original message.")
        broadcast_text = None; broadcast_photo_id = None; broadcast_video_id = None
        if original_message.text: broadcast_text = original_message.text
        elif original_message.photo: broadcast_photo_id = original_message.photo[-1].file_id
        elif original_message.video: broadcast_video_id = original_message.video.file_id
        else: raise ValueError("Message has no text or supported media.")
        bot.answer_callback_query(call.id, "📢 Starting broadcast...")
        bot.edit_message_text(f"📢 Broadcasting to {len(active_users)} users...", chat_id, call.message.message_id, reply_markup=None)
        thread = threading.Thread(target=execute_broadcast, args=(
            broadcast_text, broadcast_photo_id, broadcast_video_id,
            original_message.caption if (broadcast_photo_id or broadcast_video_id) else None, chat_id))
        thread.start()
    except ValueError as ve:
        bot.edit_message_text(f"❌ Error: {ve}", chat_id, call.message.message_id, reply_markup=None)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "📢 Broadcast cancelled.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

def execute_broadcast(broadcast_text, photo_id, video_id, caption, admin_chat_id):
    sent_count = 0; failed_count = 0; blocked_count = 0
    start_exec_time = time.time()
    users_to_broadcast = list(active_users); total_users = len(users_to_broadcast)
    logger.info(f"📢 Executing broadcast to {total_users} users.")
    batch_size = 25; delay_batches = 1.5
    for i, user_id_bc in enumerate(users_to_broadcast):
        try:
            if broadcast_text: bot.send_message(user_id_bc, broadcast_text, parse_mode='Markdown')
            elif photo_id: bot.send_photo(user_id_bc, photo_id, caption=caption, parse_mode='Markdown' if caption else None)
            elif video_id: bot.send_video(user_id_bc, video_id, caption=caption, parse_mode='Markdown' if caption else None)
            sent_count += 1
        except telebot.apihelper.ApiTelegramException as e:
            err_desc = str(e).lower()
            if any(s in err_desc for s in ["bot was blocked", "user is deactivated", "chat not found"]):
                blocked_count += 1
            elif "flood control" in err_desc or "too many requests" in err_desc:
                retry_after = 5; match = re.search(r"retry after (\d+)", err_desc)
                if match: retry_after = int(match.group(1)) + 1
                time.sleep(retry_after)
                try:
                    if broadcast_text: bot.send_message(user_id_bc, broadcast_text, parse_mode='Markdown')
                    sent_count += 1
                except: failed_count +=1
            else: failed_count += 1
        except Exception as e: failed_count += 1
        if (i + 1) % batch_size == 0 and i < total_users - 1:
            time.sleep(delay_batches)
        elif i % 5 == 0: time.sleep(0.2)
    duration = round(time.time() - start_exec_time, 2)
    result_msg = (f"📢 **Broadcast Complete!**\n\n"
                  f"✅ Sent: {sent_count}\n"
                  f"❌ Failed: {failed_count}\n"
                  f"🚫 Blocked/Inactive: {blocked_count}\n"
                  f"🎯 Targets: {total_users}\n"
                  f"⏱️ Duration: {duration}s")
    try: bot.send_message(admin_chat_id, result_msg, parse_mode='Markdown')
    except: pass

def process_broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text and message.text.lower() == '/cancel': bot.reply_to(message, "❌ Broadcast cancelled."); return
    broadcast_content = message.text
    if not broadcast_content and not (message.photo or message.video or message.document or message.sticker or message.voice or message.audio):
         bot.reply_to(message, "⚠️ Cannot broadcast empty message.")
         msg = bot.send_message(message.chat.id, "📢 Send broadcast message or /cancel.")
         bot.register_next_step_handler(msg, process_broadcast_message)
         return
    target_count = len(active_users)
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_broadcast_{message.message_id}"),
               types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast"))
    preview_text = broadcast_content[:1000].strip() if broadcast_content else "(Media message)"
    bot.reply_to(message, f"📢 Confirm Broadcast:\n\n```\n{preview_text}\n```\nTo **{target_count}** users. Sure?", reply_markup=markup, parse_mode='Markdown')

# ============================================================
# ============== EXISTING ADMIN CALLBACKS ====================
# ============================================================
def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔐 Enter User ID to promote to Admin.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "👑 Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id <= 0 or new_admin_id == OWNER_ID: raise ValueError()
        if new_admin_id in admin_ids: bot.reply_to(message, f"User already Admin."); return
        add_admin_db(new_admin_id)
        bot.reply_to(message, f"✅ User `{new_admin_id}` promoted to Admin.")
        try: bot.send_message(new_admin_id, "👑 Congrats! You are now an Admin.")
        except: pass
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID.")
        msg = bot.send_message(message.chat.id, "🔐 Enter User ID to promote or /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔐 Enter User ID of Admin to remove.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "👑 Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        admin_id_remove = int(message.text.strip())
        if admin_id_remove == OWNER_ID: bot.reply_to(message, "👑 Owner cannot remove self."); return
        if admin_id_remove not in admin_ids: bot.reply_to(message, f"User not Admin."); return
        if remove_admin_db(admin_id_remove):
            bot.reply_to(message, f"✅ Admin `{admin_id_remove}` removed.")
            try: bot.send_message(admin_id_remove, "You are no longer an Admin.")
            except: pass
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID.")
        msg = bot.send_message(message.chat.id, "🔐 Enter Admin ID to remove or /cancel.")
        bot.register_next_step_handler(msg, process_remove_admin_id)

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    try:
        admin_list_str = ""
        for aid in sorted(list(admin_ids)):
            if aid == OWNER_ID: admin_list_str += f"👑 `{aid}` (Owner)\n"
            else: admin_list_str += f"👤 `{aid}`\n"
        if not admin_list_str: admin_list_str = "😕 No Owner/Admins configured!"
        bot.edit_message_text(f"👑 **Current Admins:**\n\n{admin_list_str}", call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel(), parse_mode='Markdown')
    except Exception as e: logger.error(f"❌ Error listing admins: {e}")

def add_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔐 Enter User ID & days\nExample: `123456789 30`\n/cancel", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_add_subscription_details)

def process_add_subscription_details(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Format: user_id days")
        sub_user_id = int(parts[0].strip()); days = int(parts[1].strip())
        current_expiry = user_subscriptions.get(sub_user_id, {}).get('expiry')
        start_date_new_sub = datetime.now()
        if current_expiry and current_expiry > start_date_new_sub: start_date_new_sub = current_expiry
        new_expiry = start_date_new_sub + timedelta(days=days)
        save_subscription(sub_user_id, new_expiry)
        bot.reply_to(message, f"✅ Sub for `{sub_user_id}` by {days} days.\nNew expiry: {new_expiry:%Y-%m-%d}")
        try: bot.send_message(sub_user_id, f"💎 Sub activated! Expires: {new_expiry:%Y-%m-%d}.")
        except: pass
    except ValueError as e:
        bot.reply_to(message, f"❌ Invalid: {e}")
        msg = bot.send_message(message.chat.id, "🔐 Enter User ID & days, or /cancel.")
        bot.register_next_step_handler(msg, process_add_subscription_details)

def remove_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔐 Enter User ID to remove\n/cancel")
    bot.register_next_step_handler(msg, process_remove_subscription_id)

def process_remove_subscription_id(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        sub_user_id_remove = int(message.text.strip())
        if sub_user_id_remove not in user_subscriptions:
            bot.reply_to(message, f"ℹ️ User no active sub."); return
        remove_subscription_db(sub_user_id_remove)
        bot.reply_to(message, f"✅ Sub for `{sub_user_id_remove}` removed.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID.")
        msg = bot.send_message(message.chat.id, "🔐 Enter User ID or /cancel.")
        bot.register_next_step_handler(msg, process_remove_subscription_id)

def list_subscriptions_callback(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⛔ Admin only.", show_alert=True); return
    if not user_subscriptions:
        bot.edit_message_text("😕 No active subscriptions found.", call.message.chat.id, call.message.message_id, reply_markup=create_subscription_panel())
        return
    subs_text = "**💎 Active Subscriptions:**\n\n"
    for user_id, sub_info in list(user_subscriptions.items())[:20]:
        expiry = sub_info.get('expiry')
        if expiry:
            days_left = (expiry - datetime.now()).days if expiry > datetime.now() else 0
            status = "🟢 Active" if expiry > datetime.now() else "🔴 Expired"
            subs_text += f"🆔 User {user_id}\n🟢 Status: {status}\n⏳ Expires: {expiry.strftime('%Y-%m-%d')} ({days_left} days remaining)\n\n"
    if len(user_subscriptions) > 20: subs_text += f"\n... and {len(user_subscriptions) - 20} more"
    bot.edit_message_text(subs_text, call.message.chat.id, call.message.message_id, reply_markup=create_subscription_panel(), parse_mode='Markdown')

def check_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💎 Enter User ID to check sub.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_check_subscription_id)

def process_check_subscription_id(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        sub_user_id_check = int(message.text.strip())
        if sub_user_id_check in user_subscriptions:
            expiry_dt = user_subscriptions[sub_user_id_check].get('expiry')
            if expiry_dt:
                if expiry_dt > datetime.now():
                    days_left = (expiry_dt - datetime.now()).days
                    bot.reply_to(message, f"✅ Active sub.\nExpires: {expiry_dt:%Y-%m-%d} ({days_left} days left).")
                else:
                    bot.reply_to(message, f"⚠️ Expired sub.")
                    remove_subscription_db(sub_user_id_check)
        else: bot.reply_to(message, f"ℹ️ No active sub record.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid ID.")
        msg = bot.send_message(message.chat.id, "💎 Enter User ID or /cancel.")
        bot.register_next_step_handler(msg, process_check_subscription_id)

def user_management_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("👥 User Management\nSelect action:", call.message.chat.id, call.message.message_id, reply_markup=create_user_management_menu())
    except: pass

def ban_user_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🚫 Enter User ID and reason (e.g., `12345678 Spamming`)\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) < 2: bot.reply_to(message, "⚠️ Format: `user_id reason`"); return
        user_id = int(parts[0]); reason = ' '.join(parts[1:])
        if user_id == OWNER_ID or user_id in admin_ids: bot.reply_to(message, "⚠️ Cannot ban admin."); return
        if ban_user_db(user_id, reason, message.from_user.id):
            bot.reply_to(message, f"✅ User `{user_id}` banned.\nReason: {reason}")
            for file_name, _ in user_files.get(user_id, []):
                script_key = f"{user_id}_{file_name}"
                if script_key in bot_scripts:
                    kill_process_tree(bot_scripts[script_key]); del bot_scripts[script_key]
            try: bot.send_message(user_id, f"🚫 You have been banned.\nReason: {reason}")
            except: pass
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID.")

def unban_user_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✅ Enter User ID to unban\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        user_id = int(message.text.strip())
        if user_id not in banned_users: bot.reply_to(message, f"ℹ️ User is not banned."); return
        if unban_user_db(user_id):
            bot.reply_to(message, f"✅ User `{user_id}` unbanned.")
            try: bot.send_message(user_id, "✅ Your ban has been lifted.")
            except: pass
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID.")

def user_info_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👤 Enter User ID to get info\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_user_info)

def process_user_info(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        user_id = int(message.text.strip())
        info_parts = [f"👤 **User ID:** `{user_id}`"]
        if user_id == OWNER_ID: info_parts.append("👑 **Status:** Owner")
        elif user_id in admin_ids: info_parts.append("🛡️ **Status:** Admin")
        elif user_id in banned_users: info_parts.append("🚫 **Status:** Banned")
        elif user_id in user_subscriptions:
            expiry = user_subscriptions[user_id].get('expiry')
            if expiry and expiry > datetime.now():
                days_left = (expiry - datetime.now()).days
                info_parts.append(f"💎 **Status:** Premium (Expires in {days_left} days)")
            else: info_parts.append("🆓 **Status:** Free User")
        else: info_parts.append("🆓 **Status:** Free User")
        file_count = get_user_file_count(user_id)
        file_limit = get_user_file_limit(user_id)
        info_parts.append(f"📁 **Files:** {file_count}/{file_limit if file_limit != float('inf') else 'Unlimited'}")
        credits = user_credits.get(user_id, 0)
        info_parts.append(f"🪙 **Credits:** {credits}")
        refs = len(referrals_data.get(user_id, []))
        info_parts.append(f"👥 **Referrals:** {refs}")
        if user_id in user_limits: info_parts.append(f"⚙️ **Custom Limit:** {user_limits[user_id]}")
        running_scripts = sum(1 for file_name, _ in user_files.get(user_id, []) if is_bot_running(user_id, file_name))
        info_parts.append(f"🤖 **Running Scripts:** {running_scripts}")
        bot.reply_to(message, "\n".join(info_parts), parse_mode='Markdown')
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID.")

def all_users_callback(call):
    bot.answer_callback_query(call.id)
    try:
        if not active_users:
            bot.edit_message_text("👥 No active users yet.", call.message.chat.id, call.message.message_id); return
        users_list = list(active_users)
        chunk_size = 20
        total_pages = (len(users_list) + chunk_size - 1) // chunk_size
        display_users_list(call.message.chat.id, call.message.message_id, users_list, 0, total_pages, chunk_size)
    except Exception as e: logger.error(f"❌ Error: {e}")

def display_users_list(chat_id, message_id, users_list, page, total_pages, chunk_size):
    start_idx = page * chunk_size
    end_idx = min(start_idx + chunk_size, len(users_list))
    user_chunk = users_list[start_idx:end_idx]
    message_text = f"👥 **Active Users** (Page {page + 1}/{total_pages})\n\n"
    for i, user_id in enumerate(user_chunk, start=start_idx + 1):
        if user_id == OWNER_ID: status = "👑"
        elif user_id in admin_ids: status = "🛡️"
        elif user_id in banned_users: status = "🚫"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): status = "💎"
        else: status = "🆓"
        message_text += f"{i}. `{user_id}` {status}\n"
    markup = types.InlineKeyboardMarkup(row_width=3)
    if total_pages > 1:
        page_buttons = []
        if page > 0: page_buttons.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"users_page_{page-1}"))
        page_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1: page_buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"users_page_{page+1}"))
        markup.row(*page_buttons)
    markup.row(types.InlineKeyboardButton("🔙 Back", callback_data='adm_users'))
    try: bot.edit_message_text(message_text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('users_page_'))
def handle_users_page(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin only.", show_alert=True); return
    try:
        page = int(call.data.split('_')[2])
        users_list = list(active_users)
        chunk_size = 20
        total_pages = (len(users_list) + chunk_size - 1) // chunk_size
        if 0 <= page < total_pages:
            bot.answer_callback_query(call.id)
            display_users_list(call.message.chat.id, call.message.message_id, users_list, page, total_pages, chunk_size)
    except Exception as e: logger.error(f"❌ Error: {e}")

def set_user_limit_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔧 Enter User ID and new limit (e.g., `12345678 50`)\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_set_user_limit)

def process_set_user_limit(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Format: user_id limit")
        user_id = int(parts[0]); limit = int(parts[1])
        if set_user_limit_db(user_id, limit, message.from_user.id):
            bot.reply_to(message, f"✅ Set file limit {limit} for `{user_id}`")
            try: bot.send_message(user_id, f"⚙️ Your file upload limit has been set to {limit}")
            except: pass
    except ValueError as e: bot.reply_to(message, f"⚠️ Invalid: {e}")

def remove_user_limit_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🗑️ Enter User ID to remove custom limit\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_remove_user_limit)

def process_remove_user_limit(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⛔ Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    try:
        user_id = int(message.text.strip())
        if user_id not in user_limits: bot.reply_to(message, f"ℹ️ User has no custom limit."); return
        if remove_user_limit_db(user_id):
            bot.reply_to(message, f"✅ Removed custom limit for `{user_id}`")
            try: bot.send_message(user_id, "⚙️ Your custom file limit has been removed")
            except: pass
    except ValueError: bot.reply_to(message, "❌ Invalid user ID.")

def admin_settings_callback(call):
    bot.answer_callback_query(call.id)
    try: bot.edit_message_text("⚙️ Admin Settings\nSelect action:", call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu())
    except: pass

def system_info_callback(call):
    bot.answer_callback_query(call.id)
    try:
        import platform
        info_parts = ["🤖 **Bot Information:**"]
        info_parts.append(f"• Python: {platform.python_version()}")
        info_parts.append(f"• Platform: {platform.platform()}")
        info_parts.append("\n💻 **System Information:**")
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            info_parts.append(f"• CPU Usage: {cpu_percent}%")
            info_parts.append(f"• Memory: {memory.percent}% used")
            info_parts.append(f"• Disk: {disk.percent}% used")
        except Exception as e: info_parts.append(f"• System stats error")
        info_parts.append("\n📊 **Bot Statistics:**")
        info_parts.append(f"• Active Users: {len(active_users)}")
        info_parts.append(f"• Running Scripts: {len(bot_scripts)}")
        info_parts.append(f"• Total Files: {sum(len(files) for files in user_files.values())}")
        info_parts.append(f"• Bot Status: {'🔒 Locked' if bot_locked else '🔓 Unlocked'}")
        bot.edit_message_text("\n".join(info_parts), call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu(), parse_mode='Markdown')
    except: pass

def bot_performance_callback(call):
    bot.answer_callback_query(call.id)
    try:
        perf_parts = ["📈 **Bot Performance Metrics:**"]
        running_scripts = len(bot_scripts)
        total_files = sum(len(files) for files in user_files.values())
        perf_parts.append(f"• Running Scripts: {running_scripts}")
        perf_parts.append(f"• Total Scripts: {total_files}")
        uptime_pct = (running_scripts / total_files * 100) if total_files > 0 else 0.0
        perf_parts.append(f"• Uptime Ratio: {uptime_pct:.1f}%")
        try:
            bot_process = psutil.Process()
            memory_usage = bot_process.memory_info().rss / 1024 / 1024
            perf_parts.append(f"\n💊 **Resource Usage:**")
            perf_parts.append(f"• Memory: {memory_usage:.1f} MB")
        except: pass
        perf_parts.append(f"\n🗄️ **Database:**")
        perf_parts.append(f"• Users: {len(active_users)}")
        perf_parts.append(f"• Subscriptions: {len(user_subscriptions)}")
        perf_parts.append(f"• Banned: {len(banned_users)}")
        perf_parts.append(f"• Credits tracked: {len(user_credits)}")
        bot.edit_message_text("\n".join(perf_parts), call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu(), parse_mode='Markdown')
    except: pass

def cleanup_files_callback(call):
    bot.answer_callback_query(call.id, "🧹 Cleaning up...")
    try:
        cleaned_dirs = 0; cleaned_files = 0
        for user_dir in os.listdir(UPLOAD_BOTS_DIR):
            user_path = os.path.join(UPLOAD_BOTS_DIR, user_dir)
            if os.path.isdir(user_path):
                if not os.listdir(user_path):
                    try: os.rmdir(user_path); cleaned_dirs += 1
                    except: pass
                else:
                    for file_name in os.listdir(user_path):
                        if file_name.endswith('.log'):
                            file_path = os.path.join(user_path, file_name)
                            try:
                                file_age = time.time() - os.path.getmtime(file_path)
                                if file_age > 7 * 24 * 3600:
                                    os.remove(file_path); cleaned_files += 1
                            except: pass
        bot.edit_message_text(f"🧹 **Cleanup Complete:**\n• Empty dirs removed: {cleaned_dirs}\n• Old log files cleared: {cleaned_files}", call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu(), parse_mode='Markdown')
    except: pass

def install_logs_callback(call):
    bot.answer_callback_query(call.id)
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT user_id, module_name, package_name, status, install_date FROM install_logs ORDER BY install_date DESC LIMIT 20')
            logs = c.fetchall()
            conn.close()
        if not logs:
            bot.edit_message_text("📋 **No installation logs found**", call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu()); return
        log_text = "📋 **Recent Installation Logs (Last 20):**\n\n"
        for user_id, module_name, package_name, status, install_date in logs:
            status_icon = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
            log_text += f"{status_icon} `{user_id}`: {module_name} -> {package_name}\n   📅 {install_date[:19]}\n\n"
        bot.edit_message_text(log_text, call.message.chat.id, call.message.message_id, reply_markup=create_admin_settings_menu(), parse_mode='Markdown')
    except: pass

def admin_install_callback(call):
    bot.answer_callback_query(call.id)
    _logic_admin_install(call.message)

def manage_mandatory_channels_callback(call):
    bot.answer_callback_query(call.id)
    try: bot.edit_message_text("📢 Manage Mandatory Channels\nChoose desired action:", call.message.chat.id, call.message.message_id, reply_markup=create_mandatory_channels_menu())
    except: pass

def add_mandatory_channel_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📢 Send channel ID or username (example: @channel_username or -1001234567890)\n/cancel to cancel")
    bot.register_next_step_handler(msg, process_add_channel)

def process_add_channel(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⚠️ Not authorized."); return
    if message.text and message.text.lower() == '/cancel': bot.reply_to(message, "❌ Cancelled."); return
    channel_identifier = message.text.strip()
    try:
        chat = bot.get_chat(channel_identifier)
        channel_id = str(chat.id)
        channel_username = f"@{chat.username}" if chat.username else ""
        channel_name = chat.title
        try:
            bot_member = bot.get_chat_member(channel_id, bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                bot.reply_to(message, f"❌ Bot is not admin in the channel!"); return
        except:
            bot.reply_to(message, f"❌ Bot cannot access the channel!"); return
        if save_mandatory_channel(channel_id, channel_username, channel_name, message.from_user.id):
            bot.reply_to(message, f"✅ Mandatory Channel Added:\n**{channel_name}**\n{channel_username or channel_id}")
        else: bot.reply_to(message, "❌ Failed to add channel.")
    except Exception as e: bot.reply_to(message, f"❌ Error: {str(e)}")

def remove_mandatory_channel_callback(call):
    if not mandatory_channels:
        bot.answer_callback_query(call.id, "❌ No mandatory channels.", show_alert=True); return
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    for channel_id, channel_info in mandatory_channels.items():
        markup.add(types.InlineKeyboardButton(f"🗑️ {channel_info.get('name', 'Unknown')}", callback_data=f'remove_channel_{channel_id}'))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='adm_channels'))
    try: bot.edit_message_text("📢 Choose channel to delete:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    except: pass

def process_remove_channel(call):
    channel_id = call.data.replace('remove_channel_', '')
    if channel_id in mandatory_channels:
        channel_name = mandatory_channels[channel_id].get('name', 'Unknown')
        if remove_mandatory_channel_db(channel_id):
            bot.answer_callback_query(call.id, f"✅ Channel deleted: {channel_name}")
            try: bot.edit_message_text(f"✅ Mandatory channel deleted: **{channel_name}**", call.message.chat.id, call.message.message_id, reply_markup=create_mandatory_channels_menu(), parse_mode='Markdown')
            except: pass
        else: bot.answer_callback_query(call.id, "❌ Failed.", show_alert=True)
    else: bot.answer_callback_query(call.id, "❌ Not found.", show_alert=True)

def list_mandatory_channels_callback(call):
    bot.answer_callback_query(call.id)
    if not mandatory_channels: message_text = "📢 **No mandatory channels currently**"
    else:
        message_text = "📢 **Mandatory Channels:**\n\n"
        for channel_id, channel_info in mandatory_channels.items():
            message_text += f"• **{channel_info.get('name', 'Unknown')}**\n  {channel_info.get('username', 'No username') or channel_id}\n\n"
    try: bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, reply_markup=create_mandatory_channels_menu(), parse_mode='Markdown')
    except: pass

def check_subscription_status_callback(call):
    user_id = call.from_user.id
    is_subscribed, not_joined = check_mandatory_subscription(user_id)
    if is_subscribed or user_id in admin_ids:
        bot.answer_callback_query(call.id, "✅ You are subscribed to all required channels!", show_alert=True)
        try: _logic_send_welcome(call.message)
        except: back_to_main_callback(call)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all required channels yet!", show_alert=True)
        subscription_message, markup = create_subscription_check_message(not_joined)
        try: bot.edit_message_text(subscription_message, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        except: pass

# ============================================================
# ============== CLONE BOT CALLBACKS =========================
# ============================================================
def clone_create_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("❌ Cancel", callback_data="back_to_main"))
    bot.edit_message_text(
        f"🚀 **Create Clone Bot**\n\nSend your bot token from 👇\n@BotFather\n\nFormat: `1234567890:ABCdefGHi`",
        chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(chat_id, lambda msg: handle_token_input(msg, chat_id, message_id))
    bot.answer_callback_query(call.id)

def clone_remove_callback(call):
    user_id = call.from_user.id
    if user_id not in user_clones:
        bot.answer_callback_query(call.id, f"⚠️ No Clone bot found.", show_alert=True); return
    bot_username = user_clones[user_id]['bot_username']
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("✅ Remove", callback_data="clone_remove_confirm"), types.InlineKeyboardButton("❌ Cancel", callback_data="back_to_main"))
    bot.edit_message_text(f"🗑️ **Remove Clone Bot**\n\n⚠️ Remove your clone bot?\n\n🤖 Bot Name @{bot_username}\n🚀 Will be removed",
        call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

def clone_remove_confirm_callback(call):
    user_id = call.from_user.id
    if user_id not in user_clones:
        bot.answer_callback_query(call.id, f"⚠️ No clone bot found.", show_alert=True); return
    bot_username = user_clones[user_id]['bot_username']
    clone_dir = os.path.join(BASE_DIR, f'clone_{user_id}')
    if os.path.exists(clone_dir):
        try: shutil.rmtree(clone_dir)
        except Exception as e: logger.error(f"❌ Error: {e}")
    remove_clone_info(user_id)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"✅ **Clone Bot Removed!**\n\n🤖 Bot @{bot_username}\n🗑️ Successfully removed",
        call.message.chat.id, call.message.message_id, reply_markup=None, parse_mode="Markdown")

def handle_token_input(message, original_chat_id, original_message_id):
    user_id = message.from_user.id
    if message.text == '/cancel': _logic_clone_bot(message); return
    token = message.text.strip()
    if not token or len(token) < 35 or ':' not in token:
        bot.reply_to(message, "**❌ Invalid bot token!**\n\nPlease send a valid bot token from @BotFather", parse_mode="Markdown")
        return
    processing_msg = bot.reply_to(message, "🔄 Creating your bot clone...")
    try:
        test_bot = telebot.TeleBot(token)
        bot_info = test_bot.get_me()
        bot.edit_message_text(f"✅ Token validated!\n\nBot: @{bot_info.username}\nCreating clone...", processing_msg.chat.id, processing_msg.message_id)
        clone_success = create_bot_clone(user_id, token, bot_info.username)
        if clone_success:
            success_msg = f"**🎉 Bot Clone Created!**\n\n**🤖 Bot Name:** @{bot_info.username}\n**🚀 Status:** Running\n**✨ Unlimited clones available**"
            bot.edit_message_text(success_msg, processing_msg.chat.id, processing_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ Failed to create bot clone.", processing_msg.chat.id, processing_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"**❌ Bot Clone Failed**\n\nError: `{str(e)}`", processing_msg.chat.id, processing_msg.message_id, parse_mode="Markdown")

# ============================================================
# ============== AI FIX CALLBACK =============================
# ============================================================
def ai_fix_callback(call):
    if not check_subscription_and_continue(None, call): return
    try:
        _, owner_id_str, file_name = call.data.split('_', 2)
        owner_id = int(owner_id_str)
        if call.from_user.id != owner_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        bot.answer_callback_query(call.id, "AI Fix running...")
        threading.Thread(target=ai_fix_script, args=(owner_id, file_name, call.message.chat.id, call.message.message_id)).start()
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)

# ============================================================
# ============== MODEL CALLBACK ==============================
# ============================================================
def set_model_callback(call):
    user_id = call.from_user.id
    if user_id not in admin_ids:
        bot.answer_callback_query(call.id, "Not authorized.", show_alert=True); return
    model_key = call.data.split('_')[1]
    if model_key in AVAILABLE_MODELS:
        global global_model
        global_model = model_key
        bot.answer_callback_query(call.id, f"✅ Model changed to {model_key.upper()}")
        bot.edit_message_text(f"✅ AI model changed to *{model_key}* ({AVAILABLE_MODELS[model_key]})", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "Invalid model.", show_alert=True)

# ============================================================
# ============== APPROVAL CALLBACK ===========================
# ============================================================
def handle_approval_callback(call):
    if not check_subscription_and_continue(None, call): return
    admin_id = call.from_user.id
    if admin_id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Only admins can approve/reject.", show_alert=True); return
    upload_id = int(call.data.split('_')[-1])
    pending = get_pending_upload(upload_id)
    if not pending:
        bot.answer_callback_query(call.id, "⚠️ This upload request no longer exists.", show_alert=True)
        try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except: pass
        return
    user_id = pending['user_id']
    file_name = pending['file_name']
    if call.data.startswith('approve_upload_'):
        bot.answer_callback_query(call.id, "✅ Approving...")
        success = process_approved_file(upload_id, admin_chat_id=call.message.chat.id, user_message_obj=call.message)
        if success:
            try: bot.send_message(user_id, f"✅ Your file {file_name} has been approved and is now running.")
            except: pass
            try: bot.edit_message_caption(caption=stylish_text(call.message.caption + "\n\n✅ APPROVED"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            except: pass
    else:
        bot.answer_callback_query(call.id, "❌ Rejected.")
        delete_pending_upload(upload_id)
        try: bot.send_message(user_id, f"❌ Your file {file_name} was rejected by admin.\n\nAGLI BAR SE YE FILE RUN MT KARNA SIR")
        except: pass
        try: bot.edit_message_caption(caption=stylish_text(call.message.caption + "\n\n❌ REJECTED"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        except: pass

# ============================================================
# ============== PKG INSTALL CALLBACKS =======================
# ============================================================
def install_recommended_callback(call):
    if not check_subscription_and_continue(None, call): return
    bot.answer_callback_query(call.id, "Installing...")
    recommended = ["pip", "setuptools", "wheel", "requests", "numpy", "pandas", "flask", "aiohttp", "pyrogram", "python-dotenv", "beautifulsoup4", "lxml", "pillow", "matplotlib", "scipy", "scikit-learn", "pytest"]
    bot.send_message(call.message.chat.id, f"🚀 Installing {len(recommended)} packages... Please wait.")
    success = 0; failed = 0
    for pkg in recommended:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], capture_output=True, text=True)
            if result.returncode == 0: success += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.5)
    bot.send_message(call.message.chat.id, f"✅ Done.\n✅ Success: {success}\n❌ Failed: {failed}")

def cancel_install_callback(call):
    bot.answer_callback_query(call.id, "Cancelled.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

# ============================================================
# ============== GITHUB CALLBACKS ============================
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in github_data and github_data[m.from_user.id].get('step') == 'url')
def github_get_url(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if message.text and message.text.lower() == '/cancel':
        del github_data[user_id]
        bot.reply_to(message, "❌ Cancelled."); return
    url = message.text.strip()
    try:
        owner, repo, branch = parse_github_url(url)
    except Exception as e:
        bot.reply_to(message, f"❌ Invalid URL: {e}"); return
    github_data[user_id]['url'] = url
    github_data[user_id]['owner'] = owner
    github_data[user_id]['repo'] = repo
    github_data[user_id]['branch'] = branch
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔒 Private", callback_data=f"github_private_{user_id}"), types.InlineKeyboardButton("🌐 Public", callback_data=f"github_public_{user_id}"))
    bot.reply_to(message, "Is this a private repository?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('github_private_') or call.data.startswith('github_public_'))
def github_repo_type(call):
    user_id = int(call.data.split('_')[-1])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "Not for you", show_alert=True); return
    if user_id not in github_data:
        bot.answer_callback_query(call.id, "Session expired", show_alert=True); return
    if call.data.startswith('github_private_'):
        github_data[user_id]['step'] = 'token'
        bot.edit_message_text("🔑 Send your GitHub personal access token (with `repo` scope).\nSend /cancel to abort.", call.message.chat.id, call.message.message_id)
    else:
        github_data[user_id]['token'] = None
        _process_github_download(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.from_user.id in github_data and github_data[m.from_user.id].get('step') == 'token')
def github_get_token(message):
    if not check_subscription_and_continue(message): return
    user_id = message.from_user.id
    if message.text and message.text.lower() == '/cancel':
        del github_data[user_id]
        bot.reply_to(message, "❌ Cancelled."); return
    token = message.text.strip()
    github_data[user_id]['token'] = token
    _process_github_download(message.chat.id, user_id)

def _process_github_download(chat_id, user_id):
    data = github_data.get(user_id)
    if not data:
        bot.send_message(chat_id, "Session expired. Start again."); return
    url = data['url']; owner = data['owner']; repo = data['repo']; branch = data['branch']; token = data.get('token')
    msg = bot.send_message(chat_id, "📥 Downloading repo...")
    time.sleep(1.5)
    bot.edit_message_text("🔍 Downloaded. Submitting for approval...", chat_id, msg.message_id)
    try:
        zip_content = download_github_repo(owner, repo, branch, token)
    except Exception as e:
        bot.edit_message_text(f"❌ Download failed: {e}", chat_id, msg.message_id)
        del github_data[user_id]; return
    file_name = f"{repo}_{branch}.zip"
    try:
        sent = bot.send_document(chat_id, io.BytesIO(zip_content), visible_file_name=file_name, caption="📤 Submitting for admin approval...")
        file_id = sent.document.file_id
        file_size = sent.document.file_size
        user_name = bot.get_chat(user_id).first_name
        user_username = bot.get_chat(user_id).username or "No username"
        extra_info = f"GitHub URL: {url}"
        upload_id = add_pending_upload(user_id=user_id, file_id=file_id, file_name=file_name, file_type='zip', file_size=file_size, user_name=user_name, user_username=user_username, extra_info=extra_info)
        if not upload_id: bot.send_message(chat_id, "❌ Internal error."); return
        for admin_id in admin_ids:
            try:
                caption = (f"📦 New GitHub repo requires approval\n"
                           f"👤 User: {user_name} (@{user_username})\n"
                           f"🆔 ID: {user_id}\n"
                           f"📦 URL: {url}\n"
                           f"📄 File: {file_name}")
                sent_admin = bot.send_document(admin_id, file_id, caption=stylish_text(caption))
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_upload_{upload_id}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_upload_{upload_id}"))
                bot.edit_message_reply_markup(admin_id, sent_admin.message_id, reply_markup=markup)
            except Exception as e: logger.error(f"Failed to notify admin: {e}")
        bot.send_message(chat_id, "✅ Submitted for admin approval.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Failed: {e}")
    finally:
        del github_data[user_id]

# ============================================================
# ================ CLEANUP ===================================
# ============================================================
def cleanup():
    logger.warning("🧹 Shutdown. Cleaning up processes...")
    script_keys_to_stop = list(bot_scripts.keys())
    if not script_keys_to_stop: logger.info("✅ No scripts running."); return
    logger.info(f"🧹 Stopping {len(script_keys_to_stop)} scripts...")
    for key in script_keys_to_stop:
        if key in bot_scripts: kill_process_tree(bot_scripts[key])
    logger.warning("✅ Cleanup finished.")

atexit.register(cleanup)

# ============================================================
# ================ MAIN ENTRY POINT ==========================
# ============================================================
if __name__ == '__main__':
    logger.info("="*50)
    logger.info("🚀 Premium Bot Starting Up...")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info(f"📁 Base Dir: {BASE_DIR}")
    logger.info(f"👑 Owner ID: {OWNER_ID}")
    logger.info(f"👥 Admins: {admin_ids}")
    logger.info(f"📢 Log Group: {LOG_GROUP_ID}")
    logger.info("="*50)
    init_db()
    load_data()
    logger.info("🔧 Starting auto-recovery worker...")
    recovery_thread = threading.Thread(target=auto_recovery_worker, daemon=True)
    recovery_thread.start()
    keep_alive()
    logger.info("🤖 Starting polling...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.critical(f"❌ Unrecoverable polling error: {e}", exc_info=True)
            logger.info("🔄 Restarting polling in 30s...")
            time.sleep(30)
        finally:
            logger.warning("🔄 Polling attempt finished.")
            time.sleep(1)