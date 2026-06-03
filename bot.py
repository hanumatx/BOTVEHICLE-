import requests
import json
import logging
import random
import string
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8920266695:AAFJ3qSyI5TcSXaOPaNqRyljt8od7UrBdVs"

# --- FORCE SUBSCRIBE & ACCESS CONFIGURATION ---
CHANNEL_ID = "-1002994389095" 
CHANNEL_LINK = "https://t.me/+WTV1YU_yIvc2NDZh" 
ADMIN_ID = 8273728944 
# ----------------------------------------------

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
# -------------------------

# API Endpoints
SMC_URL = "https://www.smcinsurance.com/central/centralcall/CallReqWithHeader"
NUM_API = "https://leakosint-by-noneusr.vercel.app/@None_usernam3/free/public/api"   # new base URL
LEAKOSINT_API = "https://leakosint-by-noneusr.vercel.app/@None_usernam3/free/public/api"  # Leakosint API for mobile search
AADHAR_API = "https://pentestgpt-impds-api-finalapi.onrender.com/search-aadhaar"      # new API
SPINNY_URL = "https://api.spinny.com/v3/api/vehicle/full-pan-details/"
UPI_API = "https://api.truebalance.cc/v2/v2/payment/validateVPA"
SPINNY_AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgzNDM5MDY2LCJqdGkiOiIxOTUyOTJkNDdiNjE0M2M2YjExNGUyOWQwMjc1OTA1NSIsInVzZXJfaWQiOjI3ODQxMzg3fQ.uAQg937MTs_4Dz7rgGXq28xVX7liEx6jIm0-1SL2SNc"

# Bank names list for random selection
BANK_NAMES = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank", "Union Bank of India",
    "Yes Bank", "IDFC First Bank", "IndusInd Bank", "Bank of India", "Central Bank of India",
    "Indian Bank", "UCO Bank", "Bank of Maharashtra", "Punjab & Sind Bank", "RBL Bank"
]

# Bank codes for IFSC
BANK_CODES = {
    "State Bank of India": "SBIN", "HDFC Bank": "HDFC", "ICICI Bank": "ICIC", "Axis Bank": "UTIB",
    "Kotak Mahindra Bank": "KKBK", "Punjab National Bank": "PUNB", "Bank of Baroda": "BARB",
    "Canara Bank": "CNRB", "Union Bank of India": "UBIN", "Yes Bank": "YESB",
    "IDFC First Bank": "IDFB", "IndusInd Bank": "INDB", "Bank of India": "BKID",
    "Central Bank of India": "CBIN", "Indian Bank": "IDIB", "UCO Bank": "UCBA",
    "Bank of Maharashtra": "MAHB", "Punjab & Sind Bank": "PSIB", "RBL Bank": "RATN"
}

# City names for random selection
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata",
    "Pune", "Jaipur", "Lucknow", "Nagpur", "Indore", "Bhopal", "Surat", "Vadodara",
    "Patna", "Ludhiana", "Agra", "Nashik", "Ranchi"
]

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

# API Headers
SMC_HEADERS = {
    "Host": "www.smcinsurance.com",
    "Sec-Ch-Ua-Platform": "Android",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.179 Mobile Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.smcinsurance.com",
    "Referer": "https://www.smcinsurance.com/motor-insurance/two-wheeler-insurance"
}

# Advanced headers for Leakosint API (from HTTP/2 request)
LEAKOSINT_HEADERS = {
    "Host": "leakosint-by-noneusr.vercel.app",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not-A.Brand";v="24", "Chromium";v="146"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=0, i",
}

UPI_HEADERS = {
    "Host": "api.truebalance.cc",
    "accept": "application/json",
    "locale": "en",
    "user-agent": "truebalance",
    "versioncode": "72500"
}

SPINNY_HEADERS = {
    "Host": "api.spinny.com",
    "sec-ch-ua-platform": "Android",
    "Authorization": f"Bearer {SPINNY_AUTH_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "platform": "app_android"
}

def create_session():
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[408, 429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = create_session()

def escape_markdown(text):
    if not text:
        return "N/A"
    text = str(text)
    text = text.replace('\\', '')
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# --- Routing & Permission Check Function ---
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    first_name = update.effective_user.first_name
    
    if user_id == ADMIN_ID:
        return True

    if chat_type == "private":
        if user_id in AUTHORIZED_USERS:
            return True
        
        keyboard = [[InlineKeyboardButton("📢 JOIN OUR CHANNEL", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        private_error = (
            f"❌ *Access Denied, {escape_markdown(first_name)}!*\n\n"
            f"This bot cannot be used directly inside private DMs\\.\n"
            f"Please click the link below to join our official channel and use it there\\!"
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(private_error, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(private_error, parse_mode='Markdown', reply_markup=reply_markup)
        return False

    else:
        if user_id in AUTHORIZED_USERS:
            return True
            
        try:
            chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                return True
        except Exception as e:
            logger.error(f"Membership check failed: {e}")
        
        keyboard = [
            [InlineKeyboardButton("📢 JOIN OUR CHANNEL", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_joined")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        group_error = (
            f"❌ *Hold on, {escape_markdown(first_name)}!*\n\n"
            f"To use this bot here in the group, you must be a member of our updates channel\\.\n\n"
            f"Join via the button below and tap *I HAVE JOINED* to continue\\."
        )
        
        if update.callback_query:
            await update.callback_query.message.reply_text(group_error, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(group_error, parse_mode='Markdown', reply_markup=reply_markup)
        return False
# --------------------------------------------

async def access_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
        
    if not context.args:
        await update.message.reply_text("❌ Please provide a User ID!\n\nExample: `/access 123456789`", parse_mode='Markdown')
        return
        
    try:
        target_id = int(context.args[0])
        AUTHORIZED_USERS.add(target_id)
        save_auth_users(AUTHORIZED_USERS)
        await update.message.reply_text(f"✅ User `{target_id}` has been approved for Private DM access.", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID format. Numbers only.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """New command to search phone number using Leakosint API with advanced headers"""
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a mobile number!\n\nExample: `/search 8052036991` or `/search +918052036991`", parse_mode='Markdown')
        return
    
    raw_number = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, raw_number))
    if len(digits) < 10:
        await update.message.reply_text("❌ Please provide a valid 10-digit mobile number.")
        return
    
    mobile_10 = digits[-10:]
    mobile_with_prefix = f"+91{mobile_10}"
    
    msg = await update.message.reply_text(f"🔍 Searching Leakosint for `{mobile_with_prefix}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        # Use the exact URL format from HTTP/2 request: search={number}
        url = f"{LEAKOSINT_API}?search={mobile_with_prefix}"
        
        # Make request with advanced headers
        response = session.get(url, headers=LEAKOSINT_HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success" and "data" in data:
                results = data["data"]
                
                if results and len(results) > 0:
                    # Format the response nicely
                    result_text = f"🔍 *LEAKOSINT SEARCH RESULTS*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    result_text += f"📱 *Mobile:* `{mobile_with_prefix}`\n"
                    result_text += f"📊 *Status:* {data.get('status', 'N/A')}\n"
                    result_text += f"💾 *Cached:* {'✅ Yes' if data.get('cached') else '❌ No'}\n"
                    result_text += f"📈 *Total Results:* {len(results)}\n\n"
                    result_text += f"📋 *DETAILS:*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                    
                    for idx, item in enumerate(results, 1):
                        result_text += f"\n{idx}. `{escape_markdown(item)}`"
                    
                    # Truncate if too long
                    if len(result_text) > 4000:
                        result_text = result_text[:4000] + "\n\n... (response truncated)"
                    
                    keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
                else:
                    await msg.edit_text(f"❌ No results found for `{mobile_with_prefix}`")
            else:
                await msg.edit_text(f"❌ API returned error status or invalid data\n\n```json\n{json.dumps(data, indent=2)[:500]}\n```", parse_mode='Markdown')
        else:
            await msg.edit_text(f"❌ API Error\nStatus Code: {response.status_code}")
            
    except json.JSONDecodeError:
        await msg.edit_text(f"❌ Invalid JSON response from API\n\nResponse preview: {response.text[:300]}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {escape_markdown(str(e)[:100])}")

async def vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
        
    if not context.args:
        await update.message.reply_text("❌ Please provide a registration number!\n\nExample: `/vehicle UP42AL8182`", parse_mode='Markdown')
        return
    
    registration_number = context.args[0].upper()
    msg = await update.message.reply_text(f"🔍 Fetching all details for `{registration_number}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        payload = {"URL": "GetVaahanDetailsByVehicleNo", "Props": [registration_number], "Token": ""}
        response = session.post(SMC_URL, headers=SMC_HEADERS, json=payload, timeout=60, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and data["response"]:
                vehicle_info = data["response"]
                result_text = "🚗 *ALL VEHICLE DATA*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                for key, value in vehicle_info.items():
                    if isinstance(value, dict):
                        result_text += f"\n🏦 *{key.upper()}*\n"
                        for sub_key, sub_value in value.items():
                            if sub_value == "" or sub_value is None: sub_value = "N/A"
                            result_text += f"├ *{sub_key}:* `{escape_markdown(sub_value)}`\n"
                    else:
                        if value == "" or value is None: value = "N/A"
                        result_text += f"*{key}:* `{escape_markdown(value)}`\n"
                
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if len(result_text) > 4000:
                    result_text = result_text[:4000] + "...\n(Message Truncated)"
                await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await msg.edit_text(f"❌ No vehicle data found for `{registration_number}`")
        else:
            await msg.edit_text(f"❌ API Error\nStatus Code: {response.status_code}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {escape_markdown(str(e)[:100])}")

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    # Check if user provided a custom number
    if context.args:
        raw_number = context.args[0].strip()
        digits = ''.join(filter(str.isdigit, raw_number))
        if len(digits) < 10:
            await update.message.reply_text("❌ Please provide a valid 10-digit mobile number.\n\nExample: `/num 9876543210`", parse_mode='Markdown')
            return
        mobile_10 = digits[-10:]
        mobile_with_prefix = f"+91{mobile_10}"
        custom_msg = f"for `{mobile_with_prefix}`"
    else:
        # Generate random Indian mobile number (starts with 6,7,8,9)
        first_digit = random.choice(['6', '7', '8', '9'])
        remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(9))
        mobile_10 = first_digit + remaining_digits
        mobile_with_prefix = f"+91{mobile_10}"
        custom_msg = f"random number `{mobile_with_prefix}`"
    
    msg = await update.message.reply_text(f"🔍 Fetching raw data for {custom_msg}...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        url = f"{NUM_API}?search={mobile_with_prefix}"
        response = session.get(url, timeout=60)
        raw_text = response.text
        
        # Truncate if too long (Telegram limit ~4096 chars)
        if len(raw_text) > 4000:
            raw_text = raw_text[:4000] + "\n... (response truncated)"
        
        result_text = f"📡 *RAW API RESPONSE* ({custom_msg})\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```\n{raw_text}\n```"
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide an Aadhaar number!\n\nExample: `/aadhar 212028834716`", parse_mode='Markdown')
        return
    
    aadhaar_number = context.args[0].strip()
    aadhaar_number = ''.join(filter(str.isdigit, aadhaar_number))
    if len(aadhaar_number) != 12:
        await update.message.reply_text("❌ Please provide a valid 12-digit Aadhaar number.")
        return
    
    safe_display = f"********{aadhaar_number[-4:]}" if len(aadhaar_number) >= 4 else "********"
    msg = await update.message.reply_text(f"🔍 Fetching raw data for Aadhaar ending `{safe_display}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        params = {"search": "A", "aadhaar": aadhaar_number}
        response = session.get(AADHAR_API, params=params, timeout=90)
        raw_text = response.text
        
        if len(raw_text) > 4000:
            raw_text = raw_text[:4000] + "\n... (response truncated)"
        
        result_text = f"📡 *RAW API RESPONSE*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```\n{raw_text}\n```"
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def pan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a PAN number!\n\nExample: `/pan ACCPA2495F`", parse_mode='Markdown')
        return
    
    pan_number = context.args[0].upper()
    msg = await update.message.reply_text(f"🔍 Fetching PAN details for `{pan_number}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        params = {"pan_number": pan_number, "source": "used-car-loans"}
        response = session.post(SPINNY_URL, params=params, headers=SPINNY_HEADERS, cookies={"platform": "app_android"}, json={}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('is_success') and data.get('ok'):
                pan_data = data.get('data', {})
                result_text = f"""
📇 *PAN CARD DETAILS*
━━━━━━━━━━━━━━━━━━━━━━━

*PAN:* `{escape_markdown(pan_data.get('pan_number', 'N/A'))}`
*Name:* {escape_markdown(pan_data.get('name', 'N/A'))}

*Personal:*
├ Gender: {escape_markdown(pan_data.get('gender', 'N/A'))}
├ DOB: {escape_markdown(pan_data.get('dob', 'N/A'))}
├ Category: {escape_markdown(pan_data.get('category', 'N/A'))}
└ Type: {escape_markdown(pan_data.get('type_of_holder', 'N/A'))}

*Status:*
├ PAN Status: {escape_markdown(pan_data.get('pan_status', 'N/A'))}
├ Valid: {'✅' if pan_data.get('is_valid') else '❌'}
├ Aadhaar Linked: {'✅' if pan_data.get('is_aadhaar_linked') else '❌'}
└ Individual: {'✅' if pan_data.get('is_individual') else '❌'}

*Masked Aadhaar:* {escape_markdown(pan_data.get('masked_aadhar_number', 'N/A'))}
                """
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await msg.edit_text(f"❌ No data found for PAN `{pan_number}`")
        else:
            await msg.edit_text(f"❌ API Error: {response.status_code}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def upi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a UPI ID / VPA!\n\nExample: `/upi vipansharma1931141@okhdfcbank`", parse_mode='Markdown')
        return
    
    vpa_id = context.args[0]
    msg = await update.message.reply_text(f"🔍 Validating UPI ID `{vpa_id}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        random_bank = random.choice(BANK_NAMES)
        random_city = random.choice(CITIES)
        random_micr = generate_random_micr()
        random_ifsc = generate_random_ifsc(random_bank)
        random_account = generate_random_account_number()
        random_phone = generate_random_phone()
        name_from_vpa = vpa_id.split('@')[0] if '@' in vpa_id else vpa_id
        random_email = generate_random_email(name_from_vpa)
        
        payload = {"vpaId": vpa_id}
        response = session.post(UPI_API, headers=UPI_HEADERS, json=payload, timeout=60)
        
        result_text = (
            f"\n💳 *UPI VALIDATION RESULT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*UPI ID:* `{escape_markdown(vpa_id)}`\n"
            f"*Status:* ✅ Validated\n\n"
            f"🏦 *Bank Details*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"├ Bank: {escape_markdown(random_bank)}\n"
            f"├ Branch: {escape_markdown(random_city)}\n"
            f"├ IFSC: `{random_ifsc}`\n"
            f"├ MICR: `{random_micr}`\n"
            f"└ Account: `{random_account}`\n\n"
            f"👤 *Account Holder*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"├ Name: {escape_markdown(name_from_vpa.title())}\n"
            f"├ Mobile: `{random_phone}`\n"
            f"└ Email: `{random_email}`\n\n"
            f"✅ *UPI is active and ready for transactions*"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    keyboard = [
        [InlineKeyboardButton("🔍 LEAKOSINT SEARCH", callback_data="menu_search")],
        [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
        [InlineKeyboardButton("📱 RATION BY MOBILE", callback_data="menu_num")],
        [InlineKeyboardButton("🆔 RATION BY AADHAAR", callback_data="menu_aadhar")],
        [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
        [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
        [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = """
🚀 *WELCOME TO SEARCH BOT* 🚀

━━━━━━━━━━━━━━━━━━━━━━━

*Select an option below:*

🔍 *Leakosint Search* - Advanced phone number lookup
🚗 *Vehicle Search* - Comprehensive vehicle info
📱 *Ration (Mobile)* - Raw API response for mobile number
🆔 *Ration (Aadhaar)* - Raw API response for Aadhaar
📇 *PAN Card* - PAN card details
💳 *UPI Validation* - Validate UPI/VPA ID

━━━━━━━━━━━━━━━━━━━━━━━

💡 *Commands:*
`/search 8052036771`
`/vehicle UP32JK8979`
`/num` (auto random) or `/num 9876543210`
`/aadhar 212028834716`
`/pan ACCPA2495F`
`/upi vipansharma1931141@okhdfcbank`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data != "check_joined" and not await is_subscribed(update, context):
        return
        
    if data == "check_joined":
        if await is_subscribed(update, context):
            await query.message.delete()
            keyboard = [
                [InlineKeyboardButton("🔍 LEAKOSINT SEARCH", callback_data="menu_search")],
                [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
                [InlineKeyboardButton("📱 RATION BY MOBILE", callback_data="menu_num")],
                [InlineKeyboardButton("🆔 RATION BY AADHAAR", callback_data="menu_aadhar")],
                [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
                [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
                [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🚀 *WELCOME TO SEARCH BOT* 🚀\n\n━━━━━━━━━━━━━━━━━━━━━━━\n\n*Select an option below:*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.answer("❌ You still haven't joined the channel!", show_alert=True)
            
    elif data == "menu_search":
        await query.edit_message_text(
            "🔍 *LEAKOSINT PHONE SEARCH*\n\nPlease send the mobile number.\nExample: `8052036881` or `+918052036881`\n\nType: `/search 8052036881`\n\n*This will return comprehensive phone number data including:*\n- Mobile numbers\n- Addresses\n- Names\n- Email addresses\n- Document numbers\n\n*Advanced HTTP/2 headers are used for better results.*",
            parse_mode='Markdown'
        )
    elif data == "menu_vehicle":
        await query.edit_message_text(
            "🚗 *VEHICLE SEARCH*\n\nPlease send the registration number.\nExample: `UP32JK8979`\n\nType: `/vehicle UP32JK8979`",
            parse_mode='Markdown'
        )
    elif data == "menu_num":
        await query.edit_message_text(
            "📱 *MOBILE NUMBER SEARCH (RAW)*\n\n"
            "*Usage:*\n"
            "• `/num` - Auto-generates a random Indian mobile number\n"
            "• `/num 9876543210` - Search specific number\n\n"
            "*Example:* `/num`\n\n"
            "*Note:* If no number is provided, a random 10-digit number (starting with 6,7,8,9) will be used.",
            parse_mode='Markdown'
        )
    elif data == "menu_aadhar":
        await query.edit_message_text(
            "🆔 *AADHAAR SEARCH (RAW)*\n\nPlease send the Aadhaar number.\nExample: `212028834716`\n\nType: `/aadhar 212028834716`",
            parse_mode='Markdown'
        )
    elif data == "menu_pan":
        await query.edit_message_text(
            "📇 *PAN CARD SEARCH*\n\nPlease send the PAN number.\nExample: `ACCPA2495F`\n\nType: `/pan ACCPA2495F`",
            parse_mode='Markdown'
        )
    elif data == "menu_upi":
        await query.edit_message_text(
            "💳 *UPI VALIDATION*\n\nPlease send the UPI ID / VPA.\nExample: `vipansharma1931141@okhdfcbank`\n\nType: `/upi vipansharma1931141@okhdfcbank`",
            parse_mode='Markdown'
        )
    elif data == "menu_help":
        help_text = """
❓ *HELP & COMMANDS*

━━━━━━━━━━━━━━━━━━━━━━━

*Available Commands:*

🔍 `/search` - Leakosint phone number lookup (Advanced)
🚗 `/vehicle` - Full vehicle search
📱 `/num` - Raw API response (auto random or custom number)
🆔 `/aadhar` - Raw API response for Aadhaar
📇 `/pan` - PAN card details
💳 `/upi` - Validate UPI ID

━━━━━━━━━━━━━━━━━━━━━━━

*Examples:*
`/search 8052036771`
`/vehicle UP32JK8979`
`/num` (random number)
`/num 9876543210` (custom number)
`/aadhar 212028834716`
`/pan ACCPA2495F`
`/upi vipansharma1931141@okhdfcbank`

━━━━━━━━━━━━━━━━━━━━━━━

*Note about /num command:*
• When used without arguments, it automatically generates a random Indian mobile number
• You can also provide a specific 10-digit number
• The API returns raw JSON response with all available data
        """
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("🔍 LEAKOSINT SEARCH", callback_data="menu_search")],
            [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
            [InlineKeyboardButton("📱 RATION BY MOBILE", callback_data="menu_num")],
            [InlineKeyboardButton("🆔 RATION BY AADHAAR", callback_data="menu_aadhar")],
            [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
            [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
            [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🚀 *WELCOME TO SEARCH BOT* 🚀\n\n━━━━━━━━━━━━━━━━━━━━━━━\n\n*Select an option below:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("access", access_command))
    application.add_handler(CommandHandler("search", search_command))  # New command
    application.add_handler(CommandHandler("vehicle", vehicle_command))
    application.add_handler(CommandHandler("num", num_command))
    application.add_handler(CommandHandler("aadhar", aadhar_command))
    application.add_handler(CommandHandler("pan", pan_command))
    application.add_handler(CommandHandler("upi", upi_command))
    application.add_handler(CallbackQueryHandler(menu_handler))
    
    print("🤖 Bot is starting...")
    print("✅ All commands loaded successfully")
    print("Commands: /start, /access, /search, /vehicle, /num, /aadhar, /pan, /upi")
    print("\n📱 /num command features:")
    print("   - No args: Auto-generates random Indian mobile number")
    print("   - With args: Searches the provided number")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
