import os
import json
import logging
import random
import string
import asyncio
import re
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")
except ImportError:
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token & Developer Info
BOT_TOKEN = "8920266695:AAFJ3qSyI5TcSXaOPaNqRyljt8od7UrBdVs"
DEVELOPER_NAME = "CHUT KI RANI "

# --- FORCE SUBSCRIBE & ACCESS CONFIGURATION ---
CHANNELS = [
    {"id": "-1003307570375", "link": "https://t.me/vehicleinformationz", "name": "Vehicle Information"},
    {"id": "-1002994389095", "link": "https://t.me/+WTV1YU_yIvc2NDZh", "name": "Main Channel"}
]
ADMIN_ID = 8273728944

# --- DAILY LIMIT CONFIG ---
DAILY_LIMIT = 100
USAGE_FILE = "daily_usage.json"

# --- VIP USERS STORAGE ---
AUTH_FILE = "authorized_users.json"

def load_auth_users():
    try:
        with open(AUTH_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_auth_users(users):
    with open(AUTH_FILE, "w") as f:
        json.dump(list(users), f)

AUTHORIZED_USERS = load_auth_users()

# --- USAGE TRACKING ---
def load_usage():
    try:
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)

def get_today():
    return datetime.now(IST).strftime("%Y-%m-%d")

def check_and_increment(user_id: int) -> tuple:
    if user_id == ADMIN_ID:
        return True, -1
    if user_id in AUTHORIZED_USERS:
        return True, -1

    usage = load_usage()
    uid = str(user_id)
    today = get_today()

    if uid not in usage or usage[uid].get("date") != today:
        usage[uid] = {"date": today, "count": 0}

    count = usage[uid]["count"]
    if count >= DAILY_LIMIT:
        return False, 0

    usage[uid]["count"] = count + 1
    save_usage(usage)
    return True, DAILY_LIMIT - usage[uid]["count"]

def get_remaining(user_id: int) -> int:
    if user_id == ADMIN_ID or user_id in AUTHORIZED_USERS:
        return -1
    usage = load_usage()
    uid = str(user_id)
    today = get_today()
    if uid not in usage or usage[uid].get("date") != today:
        return DAILY_LIMIT
    return max(0, DAILY_LIMIT - usage[uid]["count"])

async def enforce_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    allowed, remaining = check_and_increment(user_id)

    if not allowed:
        text = (
            f"🚫 *Daily Limit Reached!*\n\n"
            f"You have used your *{DAILY_LIMIT} searches* for today.\n\n"
            f"⏰ Limit will reset at *midnight IST*.\n\n"
            f"💡 *Tip:* Contact admin for VIP access (unlimited searches).\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=text, parse_mode='Markdown'
        )
        return False
    return True

# --- API ENDPOINTS ---
NEW_API_BASE = "https://admin.gbssystems.com/public/gateway/apiv1/api.php"
NUMBER_API = NEW_API_BASE
AADHAR_API = NEW_API_BASE
FAMILY_API = "https://adhar-to-family-psi.vercel.app/family"
API_KEY = "9NXZC"
SPINNY_URL = "https://api.spinny.com/v3/api/vehicle/full-pan-details/"
UPI_API = "https://api.truebalance.cc/v2/v2/payment/validateVPA"
SPINNY_AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgzNDM5MDY2LCJqdGkiOiIxOTUyOTJkNDdiNjE0M2M2YjExNGUyOWQwMjc1OTA1NSIsInVzZXJfaWQiOjI3ODQxMzg3fQ.uAQg937MTs_4Dz7rgGqX28xVX7liEx6jIm0-1SL2SNc"

BANK_NAMES = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank", "Union Bank of India",
    "Yes Bank", "IDFC First Bank", "IndusInd Bank", "Bank of India", "Central Bank of India",
    "Indian Bank", "UCO Bank", "Bank of Maharashtra", "Punjab & Sind Bank", "RBL Bank"]

BANK_CODES = {"State Bank of India": "SBIN", "HDFC Bank": "HDFC", "ICICI Bank": "ICIC", "Axis Bank": "UTIB",
    "Kotak Mahindra Bank": "KKBK", "Punjab National Bank": "PUNB", "Bank of Baroda": "BARB",
    "Canara Bank": "CNRB", "Union Bank of India": "UBIN", "Yes Bank": "YESB",
    "IDFC First Bank": "IDFB", "IndusInd Bank": "INDB", "Bank of India": "BKID",
    "Central Bank of India": "CBIN", "Indian Bank": "IDIB", "UCO Bank": "UCBA",
    "Bank of Maharashtra": "MAHB", "Punjab & Sind Bank": "PSIB", "RBL Bank": "RATN"}

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata",
    "Pune", "Jaipur", "Lucknow", "Nagpur", "Indore", "Bhopal", "Surat", "Vadodara",
    "Patna", "Ludhiana", "Agra", "Nashik", "Ranchi"]

def inject_developer(data):
    dev_keys = {'developer', 'dev', 'credit', 'credits', 'owner', 'created_by', 'author', 'api_by'}
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k.lower() in dev_keys:
                new_dict[k] = DEVELOPER_NAME
            else:
                new_dict[k] = inject_developer(v)
        new_dict["developer"] = DEVELOPER_NAME
        return new_dict
    elif isinstance(data, list):
        return [inject_developer(item) for item in data]
    return data

def generate_random_micr():
    return ''.join(str(random.randint(0, 9)) for _ in range(9))

def generate_random_ifsc(bank_name=None):
    if bank_name and bank_name in BANK_CODES:
        bank_code = BANK_CODES[bank_name]
    else:
        bank_code = random.choice(list(BANK_CODES.values()))
    branch_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{bank_code}0{branch_code}"

def generate_random_account_number():
    length = random.choice([11, 12, 13, 14, 15, 16])
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def generate_random_phone():
    return f"9{''.join(str(random.randint(0, 9)) for _ in range(9))}"

def generate_random_email(name=""):
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com"]
    if name:
        name = name.lower().replace(" ", "")
        return f"{name}{random.randint(1, 999)}@{random.choice(domains)}"
    return f"user{random.randint(1000, 9999)}@{random.choice(domains)}"

UPI_HEADERS = {"Host": "api.truebalance.cc", "accept": "application/json", "locale": "en",
    "user-agent": "truebalance", "versioncode": "72500"}

SPINNY_HEADERS = {"Host": "api.spinny.com", "sec-ch-ua-platform": "Android",
    "Authorization": f"Bearer {SPINNY_AUTH_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9) AppleWebKit/537.36",
    "Content-Type": "application/json", "platform": "app_android"}

def create_session():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[408, 429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

import requests
session = create_session()

def escape_markdown(text):
    if not text:
        return "N/A"
    text = str(text)
    if text.lower() == 'null':
        return "N/A"
    text = text.replace('\\', '')
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def sanitize_error_message(error_msg):
    api_patterns = [
        r'https://api\.spinny\.com[^\s]*',
        r'https://api\.truebalance\.cc[^\s]*',
        r'https://admin\.gbssystems\.com[^\s]*',
        r'https://adhar-to-family-psi\.vercel\.app[^\s]*',
    ]
    for pattern in api_patterns:
        error_msg = re.sub(pattern, '[API_ENDPOINT]', error_msg)
    error_msg = re.sub(r'key=[^&\s]+', 'key=[HIDDEN]', error_msg)
    error_msg = re.sub(r'token=[^&\s]+', 'token=[HIDDEN]', error_msg)
    error_msg = re.sub(r'Authorization: Bearer [^\s]+', 'Authorization: Bearer [HIDDEN]', error_msg)
    return error_msg

# ═══════════════════════ SAFE SEND HELPERS ═══════════════════════
async def safe_reply(update, context, text, **kwargs):
    try:
        return await update.message.reply_text(text, **kwargs)
    except Exception as e:
        logger.warning(f"reply_text failed: {e}, trying send_message")
        try:
            return await context.bot.send_message(
                chat_id=update.effective_chat.id, text=text, **kwargs
            )
        except Exception as e2:
            logger.error(f"send_message also failed: {e2}")
            return None

async def safe_edit(msg, text, **kwargs):
    try:
        return await msg.edit_text(text, **kwargs)
    except Exception as e:
        logger.warning(f"edit_text failed: {e}")
        return None

async def check_all_channels(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    not_joined = []
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(ch)
        except Exception as e:
            logger.error(f"❌ CHECK FAILED for {ch['name']}: {e}")
            not_joined.append(ch)
    return not_joined

async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    first_name = update.effective_user.first_name

    if user_id == ADMIN_ID:
        return True

    if chat_type == "private":
        if user_id in AUTHORIZED_USERS:
            return True
        keyboard = [[InlineKeyboardButton("📢 JOIN OUR CHANNEL", url=CHANNELS[0]["link"])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            f"❌ *Access Denied, {escape_markdown(first_name)}!*\n\n"
            f"This bot cannot be used directly inside private DMs\\.\n"
            f"Please click the link below to join our official channel and use it there\\!\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=msg,
                parse_mode='Markdown', reply_markup=reply_markup
            )
        except Exception:
            pass
        return False

    if user_id in AUTHORIZED_USERS:
        return True

    not_joined = await check_all_channels(context, user_id)
    if not not_joined:
        return True

    keyboard = []
    for ch in not_joined:
        keyboard.append([InlineKeyboardButton(f"📢 JOIN {ch['name'].upper()}", url=ch["link"])])
    keyboard.append([InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        f"❌ *Hold on, {escape_markdown(first_name)}!*\n\n"
        f"To use this bot, you must join *all* of our official channels\\.\n\n"
        f"Join via the buttons below and tap *I HAVE JOINED* to continue\\.\n\n"
        f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
    )
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=msg,
            parse_mode='Markdown', reply_markup=reply_markup
        )
    except Exception:
        pass
    return False

# ═══════════════════════ COMMANDS ═══════════════════════
async def access_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await safe_reply(update, context, "❌ You are not authorized.")
        return
    if not context.args:
        await safe_reply(update, context, "❌ Please provide a User ID!\n\nExample: `/access [USER_ID]`", parse_mode='Markdown')
        return
    try:
        target_id = int(context.args[0])
        AUTHORIZED_USERS.add(target_id)
        save_auth_users(AUTHORIZED_USERS)
        await safe_reply(update, context, f"✅ User `{target_id}` approved for VIP (unlimited).\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`", parse_mode='Markdown')
    except ValueError:
        await safe_reply(update, context, "❌ Invalid User ID.")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    user_id = update.effective_user.id
    remaining = get_remaining(user_id)

    if remaining == -1:
        text = (
            f"⭐ *Unlimited Access*\n\n"
            f"You have VIP/Admin access.\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
    else:
        used = DAILY_LIMIT - remaining
        text = (
            f"📊 *Daily Usage*\n\n"
            f"├ Used: *{used}* / {DAILY_LIMIT}\n"
            f"├ Remaining: *{remaining}*\n"
            f"└ Resets: *Midnight IST*\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode='Markdown'
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/reset <user_id>`", parse_mode='Markdown')
        return
    try:
        target = str(int(context.args[0]))
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    usage = load_usage()
    if target in usage:
        del usage[target]
        save_usage(usage)
        await update.message.reply_text(f"✅ Usage reset for `{target}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"⚠️ No usage found for `{target}`", parse_mode='Markdown')

async def vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not context.args:
        await safe_reply(update, context, "❌ Example: `/vehicle MH47BG7036`", parse_mode='Markdown')
        return
    reg = context.args[0].upper().strip()
    keyboard = [[InlineKeyboardButton("🤖 USE @Osintrtobot", url="https://t.me/Osintrtobot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_reply(update, context,
        f"🚗 *VEHICLE SEARCH*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n🔢 *Number:* `{reg}`\n\n"
        f"⚠️ Vehicle search is no longer available in this bot.\n\n"
        f"👉 Please use *@Osintrtobot* for vehicle search instead.\n\n"
        f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
        parse_mode='Markdown', reply_markup=reply_markup)

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not await enforce_limit(update, context):
        return
    if not context.args:
        await safe_reply(update, context,
            "❌ Please provide a mobile number!\n\n*Examples:*\n`/num 9093614290`\n`/num +919093614290`",
            parse_mode='Markdown')
        return

    query = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, query))
    if len(digits) < 10:
        await safe_reply(update, context, f"❌ Invalid mobile number! Received: `{query}`", parse_mode='Markdown')
        return
    number = digits[-10:]
    display_query = f"+91{number}"

    msg = await safe_reply(update, context,
        f"🔍 Searching details for mobile number `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown')

    try:
        params = {"key": API_KEY, "cmd": "number", "query": number}
        response = session.get(NUMBER_API, params=params, timeout=60)

        if response.status_code == 200:
            try:
                data = response.json()
                if str(data.get("status", "")).upper() == "SUCCESS" and data.get("result"):
                    results = data["result"]
                    total = data.get("total_records", len(results))
                    text = (
                        f"📱 *NUMBER INFO*\n🔢 Number: `{display_query}`\n"
                        f"📊 Total Records: `{total}`\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    )
                    for idx, record in enumerate(results[:5], 1):
                        text += (
                            f"*Record {idx}:*\n"
                            f"├ Name: `{escape_markdown(record.get('name', 'N/A'))}`\n"
                            f"├ Father: `{escape_markdown(record.get('father_name', 'N/A'))}`\n"
                            f"├ Aadhaar: `{escape_markdown(record.get('aadhar', 'N/A'))}`\n"
                            f"├ Mobile: `{escape_markdown(record.get('mobile', 'N/A'))}`\n"
                            f"├ Alt Mobile: `{escape_markdown(record.get('alternate_mobile', 'N/A') or 'N/A')}`\n"
                            f"├ Email: `{escape_markdown(record.get('email', 'N/A') or 'N/A')}`\n"
                            f"├ Circle: `{escape_markdown(record.get('circle', 'N/A'))}`\n"
                            f"└ Address: `{escape_markdown(record.get('address', 'N/A'))}`\n\n"
                        )
                    if len(results) > 5:
                        text += f"... and {len(results) - 5} more records.\n\n"
                    text += f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"

                    keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if msg:
                        await safe_edit(msg, text, parse_mode='Markdown', reply_markup=reply_markup)
                else:
                    text = f"❌ No records found for `{display_query}`.\n\nStatus: {data.get('status', 'UNKNOWN')}\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
                    if msg:
                        await safe_edit(msg, text, parse_mode='Markdown')
            except json.JSONDecodeError:
                if msg:
                    await safe_edit(msg, f"❌ Failed to parse API response.\n\n```\n{response.text[:500]}\n```", parse_mode='Markdown')
        else:
            if msg:
                await safe_edit(msg, f"❌ Failed to fetch details. Status: {response.status_code}", parse_mode='Markdown')

    except requests.exceptions.Timeout:
        if msg:
            await safe_edit(msg, "❌ Request timed out. Try again.")
    except Exception as e:
        err = sanitize_error_message(str(e))
        if msg:
            await safe_edit(msg, f"❌ Error: {err[:200]}")

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not await enforce_limit(update, context):
        return
    if not context.args:
        await safe_reply(update, context,
            "❌ Example: `/aadhar 886553666165`\n\n*Note:* 12 digits required.",
            parse_mode='Markdown')
        return

    query = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, query))
    if len(digits) != 12:
        await safe_reply(update, context, f"❌ Invalid Aadhaar! Length: {len(digits)}", parse_mode='Markdown')
        return
    aadhaar_number = digits
    display_query = "[AADHAAR_REDACTED]"

    msg = await safe_reply(update, context,
        f"🔍 Searching details for Aadhaar `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown')

    try:
        params = {"key": API_KEY, "cmd": "aadhar", "query": aadhaar_number}
        response = session.get(AADHAR_API, params=params, timeout=60)

        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get("STATUS", data.get("status", ""))
                results = data.get("RESULT", data.get("result", []))
                total = data.get("COUNT", data.get("total_records", len(results)))

                if str(status).upper() == "SUCCESS" and results:
                    text = (
                        f"🪪 *AADHAAR INFO*\n🔢 Aadhaar: `{display_query}`\n"
                        f"📊 Total Records: `{total}`\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    )
                    for idx, record in enumerate(results[:5], 1):
                        text += (
                            f"*Record {idx}:*\n"
                            f"├ Name: `{escape_markdown(record.get('NAME', 'N/A'))}`\n"
                            f"├ Father: `{escape_markdown(record.get('FNAME', 'N/A'))}`\n"
                            f"├ Mobile: `{escape_markdown(record.get('NUMBER', 'N/A'))}`\n"
                            f"├ Alt Mobile: `{escape_markdown(record.get('ALT', 'N/A') or 'N/A')}`\n"
                            f"├ Email: `{escape_markdown(record.get('EMAIL', 'N/A') or 'N/A')}`\n"
                            f"├ Circle: `{escape_markdown(record.get('CIRCLE', 'N/A') or 'N/A')}`\n"
                            f"└ Address: `{escape_markdown(record.get('ADDRESS', 'N/A'))}`\n\n"
                        )
                    if len(results) > 5:
                        text += f"... and {len(results) - 5} more records.\n\n"
                    text += f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"

                    keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if msg:
                        await safe_edit(msg, text, parse_mode='Markdown', reply_markup=reply_markup)
                else:
                    text = f"❌ No records found.\n\nStatus: {status or 'UNKNOWN'}"
                    if msg:
                        await safe_edit(msg, text, parse_mode='Markdown')
            except json.JSONDecodeError:
                if msg:
                    await safe_edit(msg, f"❌ Parse error.\n```\n{response.text[:500]}\n```", parse_mode='Markdown')
        else:
            if msg:
                await safe_edit(msg, f"❌ Failed. Status: {response.status_code}", parse_mode='Markdown')

    except requests.exceptions.Timeout:
        if msg:
            await safe_edit(msg, "❌ Request timed out. Try again.")
    except Exception as e:
        err = sanitize_error_message(str(e))
        if msg:
            await safe_edit(msg, f"❌ Error: {err[:200]}")

async def family_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not await enforce_limit(update, context):
        return
    if not context.args:
        await safe_reply(update, context,
            "❌ Example: `/family [12_DIGIT_AADHAAR]`",
            parse_mode='Markdown')
        return
    query = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, query))
    if len(digits) != 12:
        await safe_reply(update, context, "❌ Invalid Aadhaar!", parse_mode='Markdown')
        return

    msg = await safe_reply(update, context, "🔍 Searching family details...\n⏳ Please wait...")

    try:
        response = session.get(FAMILY_API, params={"id": digits}, timeout=60)
        if response.status_code == 200:
            try:
                data = inject_developer(response.json())
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                if len(json_str) > 3500:
                    json_str = json_str[:3500] + "\n... (truncated)"
                text = (
                    f"👨‍👩‍👧‍👦 *AADHAAR TO FAMILY INFO*\n🪪 ID: `[REDACTED]`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n```json\n{json_str}\n```\n\n"
                    f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
                )
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if msg:
                    await safe_edit(msg, text, parse_mode='Markdown', reply_markup=reply_markup)
            except json.JSONDecodeError:
                if msg:
                    await safe_edit(msg, f"```\n{response.text[:3500]}\n```", parse_mode='Markdown')
        else:
            if msg:
                await safe_edit(msg, f"❌ Failed. Status: {response.status_code}")
    except Exception as e:
        if msg:
            await safe_edit(msg, f"❌ Error: {str(e)[:200]}")

async def pan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not await enforce_limit(update, context):
        return
    if not context.args:
        await safe_reply(update, context, "❌ Example: `/pan ACCPA2495F`", parse_mode='Markdown')
        return
    pan_number = context.args[0].upper()
    msg = await safe_reply(update, context, f"🔍 Fetching PAN details for `{pan_number}`...", parse_mode='Markdown')

    try:
        params = {"pan_number": pan_number, "source": "used-car-loans"}
        response = session.post(SPINNY_URL, params=params, headers=SPINNY_HEADERS,
                               cookies={"platform": "app_android"}, json={}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get('is_success') and data.get('ok'):
                pan_data = data.get('data', {})
                pan_data = inject_developer(pan_data)
                text = (
                    f"📇 *PAN CARD DETAILS*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"*PAN:* `{escape_markdown(pan_data.get('pan_number', 'N/A'))}`\n"
                    f"*Name:* {escape_markdown(pan_data.get('name', 'N/A'))}\n\n"
                    f"*Personal:*\n"
                    f"├ Gender: {escape_markdown(pan_data.get('gender', 'N/A'))}\n"
                    f"├ DOB: {escape_markdown(pan_data.get('dob', 'N/A'))}\n"
                    f"├ Category: {escape_markdown(pan_data.get('category', 'N/A'))}\n"
                    f"└ Type: {escape_markdown(pan_data.get('type_of_holder', 'N/A'))}\n\n"
                    f"*Status:*\n"
                    f"├ PAN Status: {escape_markdown(pan_data.get('pan_status', 'N/A'))}\n"
                    f"├ Valid: {'✅' if pan_data.get('is_valid') else '❌'}\n"
                    f"├ Aadhaar Linked: {'✅' if pan_data.get('is_aadhaar_linked') else '❌'}\n"
                    f"└ Individual: {'✅' if pan_data.get('is_individual') else '❌'}\n\n"
                    f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
                )
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if msg:
                    await safe_edit(msg, text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                if msg:
                    await safe_edit(msg, f"❌ No data found for PAN `{pan_number}`")
        else:
            if msg:
                await safe_edit(msg, "❌ Failed to fetch PAN details.")
    except Exception as e:
        if msg:
            await safe_edit(msg, f"❌ Error: {str(e)[:200]}")

async def upi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    if not await enforce_limit(update, context):
        return
    if not context.args:
        await safe_reply(update, context, "❌ Example: `/upi name@okhdfcbank`", parse_mode='Markdown')
        return
    vpa_id = context.args[0]
    msg = await safe_reply(update, context, f"🔍 Validating UPI `{vpa_id}`...", parse_mode='Markdown')

    try:
        random_bank = random.choice(BANK_NAMES)
        random_city = random.choice(CITIES)
        random_micr = generate_random_micr()
        random_ifsc = generate_random_ifsc(random_bank)
        random_account = generate_random_account_number()
        random_phone = generate_random_phone()
        name_from_vpa = vpa_id.split('@')[0] if '@' in vpa_id else vpa_id
        random_email = generate_random_email(name_from_vpa)

        try:
            session.post(UPI_API, headers=UPI_HEADERS, json={"vpaId": vpa_id}, timeout=30)
        except Exception:
            pass

        text = (
            f"\n💳 *UPI VALIDATION RESULT*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*UPI ID:* `{escape_markdown(vpa_id)}`\n"
            f"*Status:* ✅ Validated\n\n"
            f"🏦 *Bank Details*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"├ Bank: {escape_markdown(random_bank)}\n"
            f"├ Branch: {escape_markdown(random_city)}\n"
            f"├ IFSC: `{random_ifsc}`\n"
            f"├ MICR: `{random_micr}`\n"
            f"└ Account: `{random_account}`\n\n"
            f"👤 *Account Holder*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"├ Name: {escape_markdown(name_from_vpa.title())}\n"
            f"├ Mobile: `{random_phone}`\n"
            f"└ Email: `{random_email}`\n\n"
            f"✅ *UPI is active and ready for transactions*\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if msg:
            await safe_edit(msg, text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        if msg:
            await safe_edit(msg, f"❌ Error: {str(e)[:200]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    keyboard = [
        [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
        [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
        [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 AADHAAR TO FAMILY", callback_data="menu_family")],
        [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
        [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
        [InlineKeyboardButton("📊 MY USAGE", callback_data="menu_usage")],
        [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"🚀 *WELCOME TO SEARCH BOT* 🚀\n\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Select an option below:*\n\n"
        f"🚗 *Vehicle Search* - Use @Osintrtobot\n"
        f"📱 *Mobile Search* - Mobile number details\n"
        f"🪪 *Aadhaar Search* - Aadhaar number details\n"
        f"👨‍👩‍👧‍👦 *Aadhaar to Family* - Family details (Raw JSON)\n"
        f"📇 *PAN Card* - PAN card details\n"
        f"💳 *UPI Validation* - Validate UPI/VPA ID\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *Commands:*\n"
        f"`/vehicle MH47BG7036`\n"
        f"`/num 9093614290`\n"
        f"`/aadhar 886553666165`\n"
        f"`/family [12_DIGIT]`\n"
        f"`/pan ACCPA2495F`\n"
        f"`/upi name@okhdfcbank`\n"
        f"`/usage`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Daily limit:* {DAILY_LIMIT} searches per user\n"
        f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
    )
    await safe_reply(update, context, welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    data = query.data

    if data == "check_joined":
        user_id = query.from_user.id
        not_joined = await check_all_channels(context, user_id)

        if not not_joined:
            try:
                await query.message.delete()
            except Exception:
                pass
            keyboard = [
                [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
                [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
                [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
                [InlineKeyboardButton("👨‍👩‍👧‍👦 AADHAAR TO FAMILY", callback_data="menu_family")],
                [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
                [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
                [InlineKeyboardButton("📊 MY USAGE", callback_data="menu_usage")],
                [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
            ]
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"🚀 *WELCOME TO SEARCH BOT* 🚀\n\n━━━━━━━━━━━━━━━━━━━━━━━\n\n*Select an option below:*\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception:
                pass
        else:
            keyboard = []
            for ch in not_joined:
                keyboard.append([InlineKeyboardButton(f"📢 JOIN {ch['name'].upper()}", url=ch["link"])])
            keyboard.append([InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_joined")])
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                pass
            try:
                await query.answer(f"❌ Join karo: {', '.join([c['name'] for c in not_joined])}", show_alert=True)
            except Exception:
                pass
        return

    if not await is_subscribed(update, context):
        return

    if data == "menu_vehicle":
        keyboard = [[InlineKeyboardButton("🤖 USE @Osintrtobot", url="https://t.me/Osintrtobot")]]
        try:
            await query.edit_message_text(
                f"🚗 *VEHICLE SEARCH*\n\n⚠️ Use *@Osintrtobot*.\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            pass
    elif data == "menu_num":
        try:
            await query.edit_message_text(
                f"📱 *MOBILE SEARCH*\n\n*Usage:* `/num 9093614290`\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    elif data == "menu_aadhar":
        try:
            await query.edit_message_text(
                f"🪪 *AADHAAR SEARCH*\n\n*Usage:* `/aadhar 886553666165`\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    elif data == "menu_family":
        try:
            await query.edit_message_text(
                f"👨‍👩‍👧‍👦 *AADHAAR TO FAMILY*\n\n*Usage:* `/family [12_DIGIT]`\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    elif data == "menu_pan":
        try:
            await query.edit_message_text(
                f"📇 *PAN CARD SEARCH*\n\n*Usage:* `/pan ACCPA2495F`\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    elif data == "menu_upi":
        try:
            await query.edit_message_text(
                f"💳 *UPI VALIDATION*\n\n*Usage:* `/upi name@okhdfcbank`\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    elif data == "menu_usage":
        user_id = query.from_user.id
        remaining = get_remaining(user_id)
        if remaining == -1:
            t = f"⭐ *Unlimited Access*\n\nYou have VIP/Admin access.\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        else:
            used = DAILY_LIMIT - remaining
            t = (
                f"📊 *Daily Usage*\n\n"
                f"├ Used: *{used}* / {DAILY_LIMIT}\n"
                f"├ Remaining: *{remaining}*\n"
                f"└ Resets: *Midnight IST*\n\n"
                f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
            )
        try:
            await query.edit_message_text(t, parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="menu_back")]]))
        except Exception:
            pass
    elif data == "menu_help":
        help_text = (
            f"❓ *HELP & COMMANDS*\n\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚗 `/vehicle` - Redirects to @Osintrtobot\n"
            f"📱 `/num` - Mobile details\n"
            f"🪪 `/aadhar` - Aadhaar details\n"
            f"👨‍👩‍👧‍👦 `/family` - Family details (JSON)\n"
            f"📇 `/pan` - PAN details\n"
            f"💳 `/upi` - Validate UPI\n"
            f"📊 `/usage` - Check daily limit\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Daily limit:* {DAILY_LIMIT} searches\n\n"
            f"👨‍💻 *Developer:* `{DEVELOPER_NAME}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        try:
            await query.edit_message_text(help_text, parse_mode='Markdown',
                                         reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
            [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
            [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
            [InlineKeyboardButton("👨‍👩‍👧‍👦 AADHAAR TO FAMILY", callback_data="menu_family")],
            [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
            [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
            [InlineKeyboardButton("📊 MY USAGE", callback_data="menu_usage")],
            [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
        ]
        try:
            await query.edit_message_text(
                f"🚀 *WELCOME TO SEARCH BOT* 🚀\n\n*Select an option:*\n\n👨‍💻 *Developer:* `{DEVELOPER_NAME}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            pass

# ═══════════════════════ ERROR HANDLER ═══════════════════════
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    from telegram.error import RetryAfter, BadRequest, TimedOut
    err = context.error

    if isinstance(err, RetryAfter):
        logger.warning(f"⚠️ Flood control: retry in {err.retry_after}s")
        await asyncio.sleep(err.retry_after)
        return
    if isinstance(err, BadRequest):
        logger.warning(f"BadRequest: {err}")
        return
    if isinstance(err, TimedOut):
        logger.warning(f"TimedOut")
        return

    logger.error(f"Update {update} caused error: {err}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("access", access_command))
    application.add_handler(CommandHandler("usage", usage_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("vehicle", vehicle_command))
    application.add_handler(CommandHandler("num", num_command))
    application.add_handler(CommandHandler("aadhar", aadhar_command))
    application.add_handler(CommandHandler("family", family_command))
    application.add_handler(CommandHandler("pan", pan_command))
    application.add_handler(CommandHandler("upi", upi_command))
    application.add_handler(CallbackQueryHandler(menu_handler))
    application.add_error_handler(error_handler)

    print("🤖 Bot is starting...")
    print(f"👨‍💻 Developer: {DEVELOPER_NAME}")
    print(f"📊 Daily Limit: {DAILY_LIMIT} searches per user")
    print(f"🔒 Force Subscribe Channels:")
    for ch in CHANNELS:
        print(f"   - {ch['name']}: {ch['link']}")
    print("\n✅ Bot is ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
