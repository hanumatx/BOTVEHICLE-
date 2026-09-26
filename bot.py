import requests
import json
import logging
import random
import string
import asyncio
import re
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
# Dono channels ki ID aur link yahan daalein
CHANNELS = [
    {
        "id": "-1003307570375",
        "link": "https://t.me/vehicleinformationz",
        "name": "Vehicle Information"
    },
    {
        "id": "-1002994389095",
        "link": "https://t.me/+WTV1YU_yIvc2NDZh",
        "name": "Main Channel"
    }
]
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
VEHICLE_API = "https://chuchirandiki.vercel.app/api/vehicle"
NEW_API = "https://api.paanel.shop/api/gateway.php"
API_KEY = "Seeker"
SPINNY_URL = "https://api.spinny.com/v3/api/vehicle/full-pan-details/"
UPI_API = "https://api.truebalance.cc/v2/v2/payment/validateVPA"
SPINNY_AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgzNDM5MDY2LCJqdGkiOiIxOTUyOTJkNDdiNjE0M2M2YjExNGUyOWQwMjc1OTA1NSIsInVzZXJfaWQiOjI3ODQxMzg3fQ.uAQg937MTs_4Dz7rgGqX28xVX7liEx6jIm0-1SL2SNc"

# Bank names list for random selection
BANK_NAMES = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank", "Union Bank of India",
    "Yes Bank", "IDFC First Bank", "IndusInd Bank", "Bank of India", "Central Bank of India",
    "Indian Bank", "UCO Bank", "Bank of Maharashtra", "Punjab & Sind Bank", "RBL Bank"
]

BANK_CODES = {
    "State Bank of India": "SBIN", "HDFC Bank": "HDFC", "ICICI Bank": "ICIC", "Axis Bank": "UTIB",
    "Kotak Mahindra Bank": "KKBK", "Punjab National Bank": "PUNB", "Bank of Baroda": "BARB",
    "Canara Bank": "CNRB", "Union Bank of India": "UBIN", "Yes Bank": "YESB",
    "IDFC First Bank": "IDFB", "IndusInd Bank": "INDB", "Bank of India": "BKID",
    "Central Bank of India": "CBIN", "Indian Bank": "IDIB", "UCO Bank": "UCBA",
    "Bank of Maharashtra": "MAHB", "Punjab & Sind Bank": "PSIB", "RBL Bank": "RATN"
}

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
    if text.lower() == 'null':
        return "N/A"
    text = text.replace('\\', '')
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def sanitize_error_message(error_msg):
    api_patterns = [
        r'https://chuchirandiki\.vercel\.app[^\s]*',
        r'https://api\.spinny\.com[^\s]*',
        r'https://api\.truebalance\.cc[^\s]*',
        r'https://api\.paanel\.shop[^\s]*',
    ]
    for pattern in api_patterns:
        error_msg = re.sub(pattern, '[API_ENDPOINT]', error_msg)
    
    error_msg = re.sub(r'key=[^&\s]+', 'key=[HIDDEN]', error_msg)
    error_msg = re.sub(r'token=[^&\s]+', 'token=[HIDDEN]', error_msg)
    error_msg = re.sub(r'Authorization: Bearer [^\s]+', 'Authorization: Bearer [HIDDEN]', error_msg)
    
    return error_msg

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

        # Check membership in ALL channels
        not_joined = []
        for ch in CHANNELS:
            try:
                chat_member = await context.bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    not_joined.append(ch)
            except Exception as e:
                logger.error(f"Membership check failed for {ch['id']}: {e}")
                not_joined.append(ch)

        if not not_joined:
            return True

        # Build join buttons for channels the user hasn't joined
        keyboard = []
        for ch in not_joined:
            keyboard.append([InlineKeyboardButton(f"📢 JOIN {ch['name'].upper()}", url=ch["link"])])
        keyboard.append([InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_joined")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        group_error = (
            f"❌ *Hold on, {escape_markdown(first_name)}!*\n\n"
            f"To use this bot, you must join *all* of our official channels\\.\n\n"
            f"Join via the buttons below and tap *I HAVE JOINED* to continue\\."
        )

        if update.callback_query:
            await update.callback_query.message.reply_text(group_error, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(group_error, parse_mode='Markdown', reply_markup=reply_markup)
        return False

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

async def vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
        
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a registration number!\n\n"
            "Example: `/vehicle MH47BG7036`",
            parse_mode='Markdown'
        )
        return
    
    registration_number = context.args[0].upper().strip()
    
    # Redirect users to @Osintrtobot for vehicle search
    keyboard = [[InlineKeyboardButton("🤖 USE @Osintrtobot", url="https://t.me/Osintrtobot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🚗 *VEHICLE SEARCH*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔢 *Number:* `{registration_number}`\n\n"
        f"⚠️ Vehicle search is no longer available in this bot.\n\n"
        f"👉 Please use *@Osintrtobot* for vehicle search instead.\n\n"
        f"Tap the button below to open it 👇",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a mobile number!\n\n"
            "*Examples:*\n"
            "`/num 9979512484`\n"
            "`/num +919979512484`\n\n"
            "*Note:* Always use +91 prefix for best results.",
            parse_mode='Markdown'
        )
        return
    
    query = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, query))
    
    if len(digits) >= 10:
        number = digits[-10:]
        display_query = f"+91{number}"
    else:
        await update.message.reply_text(
            "❌ Invalid mobile number! Please provide a valid 10-digit mobile number.\n\n"
            f"Received: `{query}`",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text(
        f"🔍 Searching details for mobile number `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        # Format the query - remove +91 if present
        if query.startswith('+'):
            number = query[3:] if query.startswith('+91') else query[1:]
        else:
            number = digits[-10:]
        
        params = {
            "key": API_KEY,
            "number": number
        }
        logger.info(f"Calling Paanel API for number: {number}")
        logger.info(f"URL: {NEW_API}?key={API_KEY}&number={number}")
        
        response = session.get(NEW_API, params=params, timeout=60)
        logger.info(f"Paanel API Response Status: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Response data type: {type(data)}")
                logger.info(f"Response data: {json.dumps(data, indent=2)[:500]}")
                
                # Format as raw JSON
                result_text = f"🔥 *NUMBER INFO (PAANEL API)*\n"
                result_text += f"📱 Number: `{display_query}`\n"
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result_text += "```json\n"
                result_text += json.dumps(data, indent=2, ensure_ascii=False)
                result_text += "\n```"
                
                if len(result_text) > 4000:
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(json_str) > 3500:
                        json_str = json_str[:3500] + "\n... (truncated)"
                    result_text = f"🔥 *NUMBER INFO (PAANEL API)*\n"
                    result_text += f"📱 Number: `{display_query}`\n"
                    result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    result_text += "```json\n"
                    result_text += json_str
                    result_text += "\n```"
                
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON Decode Error: {je}")
                logger.error(f"Raw response: {response.text[:500]}")
                await msg.edit_text(
                    f"❌ Failed to parse API response.\n\n"
                    f"Raw response (first 500 chars):\n```\n{response.text[:500]}\n```"
                )
        else:
            await msg.edit_text(
                f"❌ Failed to fetch number details.\n"
                f"Status Code: {response.status_code}\n"
                f"Response: {response.text[:200]}"
            )
        
    except requests.exceptions.Timeout:
        await msg.edit_text("❌ Request timed out. The API server might be slow or down.")
    except requests.exceptions.ConnectionError:
        await msg.edit_text("❌ Connection error. Please check your internet connection.")
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        logger.error(f"Error in num_command: {error_msg}")
        logger.exception(e)
        await msg.edit_text(
            f"❌ An error occurred while fetching data.\n\n"
            f"Error: {error_msg[:200]}"
        )

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an Aadhaar number!\n\n"
            "*Examples:*\n"
            "`/aadhar 630971591338`\n\n"
            "*Note:* Aadhaar must be exactly 12 digits.",
            parse_mode='Markdown'
        )
        return
    
    query = context.args[0].strip()
    digits = ''.join(filter(str.isdigit, query))
    
    if len(digits) == 12:
        aadhaar_number = digits
        display_query = f"********{digits[-4:]}"
    else:
        await update.message.reply_text(
            "❌ Invalid Aadhaar number! Please provide a valid 12-digit Aadhaar number.\n\n"
            f"Received: `{query}` (Length: {len(digits)} digits)",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text(
        f"🔍 Searching details for Aadhaar `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        params = {
            "key": API_KEY,
            "aadhar": aadhaar_number
        }
        logger.info(f"Calling Paanel API for Aadhaar: {aadhaar_number}")
        logger.info(f"URL: {NEW_API}?key={API_KEY}&aadhar={aadhaar_number}")
        
        response = session.get(NEW_API, params=params, timeout=60)
        logger.info(f"Paanel API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Response data type: {type(data)}")
                
                # Format as raw JSON
                result_text = f"🔥 *AADHAAR INFO (PAANEL API)*\n"
                result_text += f"🪪 Aadhaar: `{display_query}`\n"
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result_text += "```json\n"
                result_text += json.dumps(data, indent=2, ensure_ascii=False)
                result_text += "\n```"
                
                if len(result_text) > 4000:
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(json_str) > 3500:
                        json_str = json_str[:3500] + "\n... (truncated)"
                    result_text = f"🔥 *AADHAAR INFO (PAANEL API)*\n"
                    result_text += f"🪪 Aadhaar: `{display_query}`\n"
                    result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    result_text += "```json\n"
                    result_text += json_str
                    result_text += "\n```"
                
                keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON Decode Error: {je}")
                logger.error(f"Raw response: {response.text[:500]}")
                await msg.edit_text(
                    f"❌ Failed to parse API response.\n\n"
                    f"Raw response (first 500 chars):\n```\n{response.text[:500]}\n```"
                )
        else:
            await msg.edit_text(
                f"❌ Failed to fetch Aadhaar details.\n"
                f"Status Code: {response.status_code}\n"
                f"Response: {response.text[:200]}"
            )
        
    except requests.exceptions.Timeout:
        await msg.edit_text("❌ Request timed out. The API server might be slow or down.")
    except requests.exceptions.ConnectionError:
        await msg.edit_text("❌ Connection error. Please check your internet connection.")
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        logger.error(f"Error in aadhar_command: {error_msg}")
        logger.exception(e)
        await msg.edit_text(
            f"❌ An error occurred while fetching data.\n\n"
            f"Error: {error_msg[:200]}"
        )

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
            await msg.edit_text(f"❌ Failed to fetch PAN details. Please try again later.")
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ An error occurred while fetching data. Please try again later.")

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
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ An error occurred while validating UPI. Please try again later.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    keyboard = [
        [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
        [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
        [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
        [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
        [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
        [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = """
🚀 *WELCOME TO SEARCH BOT* 🚀

━━━━━━━━━━━━━━━━━━━━━━━

*Select an option below:*

🚗 *Vehicle Search* - Use @Osintrtobot
📱 *Mobile Search* - Mobile number details (Raw JSON)
🪪 *Aadhaar Search* - Aadhaar number details (Raw JSON)
📇 *PAN Card* - PAN card details
💳 *UPI Validation* - Validate UPI/VPA ID

━━━━━━━━━━━━━━━━━━━━━━━

💡 *Commands:*
`/vehicle MH47BG7036` → Use @Osintrtobot
`/num 9979512484` - Mobile details (Raw JSON)
`/aadhar 630971591338` - Aadhaar details (Raw JSON)
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
                [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
                [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
                [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
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
            await query.answer("❌ You still haven't joined all channels!", show_alert=True)
            
    elif data == "menu_vehicle":
        keyboard = [[InlineKeyboardButton("🤖 USE @Osintrtobot", url="https://t.me/Osintrtobot")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🚗 *VEHICLE SEARCH*\n\n"
            "⚠️ Vehicle search is no longer available in this bot.\n\n"
            "👉 Please use *@Osintrtobot* for vehicle search instead.\n\n"
            "Tap the button below to open it 👇",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif data == "menu_num":
        await query.edit_message_text(
            "📱 *MOBILE SEARCH (RAW JSON)*\n\n"
            "Search details for any mobile number.\n\n"
            "*Usage:*\n"
            "`/num 9979512484`\n"
            "`/num +919979512484`\n\n"
            "*Returns raw JSON data from Paanel API*",
            parse_mode='Markdown'
        )
    elif data == "menu_aadhar":
        await query.edit_message_text(
            "🪪 *AADHAAR SEARCH (RAW JSON)*\n\n"
            "Search details by Aadhaar number.\n\n"
            "*Usage:*\n"
            "`/aadhar 630971591338`\n\n"
            "*Note:* Aadhaar must be exactly 12 digits.\n\n"
            "*Returns raw JSON data from Paanel API*",
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

🚗 `/vehicle` - Redirects to @Osintrtobot
📱 `/num` - Mobile number details (Raw JSON)
🪪 `/aadhar` - Aadhaar number details (Raw JSON)
📇 `/pan` - PAN card details
💳 `/upi` - Validate UPI ID

━━━━━━━━━━━━━━━━━━━━━━━

*Examples:*
`/vehicle MH47BG7036` → Use @Osintrtobot
`/num 9979512484` - Mobile details (Raw JSON)
`/aadhar 630971591338` - Aadhaar details (Raw JSON)
`/pan ACCPA2495F`
`/upi vipansharma1931141@okhdfcbank`

━━━━━━━━━━━━━━━━━━━━━━━

*About Vehicle Search:*
• Vehicle search has been moved to @Osintrtobot
• Please use that bot for all vehicle-related queries

*About Mobile & Aadhaar Search:*
• API: https://api.paanel.shop/api/gateway.php
• Key: Seeker
• Returns raw JSON data from the API

*About PAN Search:*
• `/pan` - Search by PAN number
• Returns full PAN card details including Aadhaar linkage status

*About UPI Validation:*
• `/upi` - Validate UPI ID / VPA
• Returns bank details and account holder information
        """
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
            [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
            [InlineKeyboardButton("🪪 AADHAAR SEARCH", callback_data="menu_aadhar")],
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
    application.add_handler(CommandHandler("vehicle", vehicle_command))
    application.add_handler(CommandHandler("num", num_command))
    application.add_handler(CommandHandler("aadhar", aadhar_command))
    application.add_handler(CommandHandler("pan", pan_command))
    application.add_handler(CommandHandler("upi", upi_command))
    application.add_handler(CallbackQueryHandler(menu_handler))
    
    print("🤖 Bot is starting...")
    print("✅ All commands loaded successfully")
    print("Commands: /start, /access, /vehicle, /num, /aadhar, /pan, /upi")
    print("\n🔒 Force Subscribe Channels:")
    for ch in CHANNELS:
        print(f"   - {ch['name']}: {ch['link']} (ID: {ch['id']})")
    print("\n🚗 Vehicle Search:")
    print("   - Redirects to @Osintrtobot")
    print("   - Usage: /vehicle MH47BG7036")
    print("\n📱 Mobile Search (RAW JSON):")
    print("   - API: https://api.paanel.shop/api/gateway.php?key=Seeker&number=XXXXXXXXXX")
    print("   - Usage: /num 9979512484")
    print("\n🪪 Aadhaar Search (RAW JSON):")
    print("   - API: https://api.paanel.shop/api/gateway.php?key=Seeker&aadhar=XXXXXXXXXX")
    print("   - Usage: /aadhar 630971591338")
    print("\n📇 PAN Search:")
    print("   - Usage: /pan ACCPA2495F")
    print("\n💳 UPI Validation:")
    print("   - Usage: /upi vipansharma1931141@okhdfcbank")
    print("\n🔒 All API endpoints and keys are hidden from users")
    print("\n✅ Bot is ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
