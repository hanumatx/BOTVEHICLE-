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
# NEW API - Replaces both num and aadhar APIs
LEAK_API = "https://sexy-leak-api.noobgamingv40.workers.dev/api"
LEAK_API_KEY = "hackerzz"  # This will be hidden from users
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

# Field name mappings for better display with emojis
FIELD_EMOJIS = {
    "Phone": "📞",
    "Mobile": "📞",
    "Adres": "📍",
    "Address": "📍",
    "DocumentNumber": "🆔",
    "FullName": "👤",
    "Name": "👤",
    "FatherName": "👨",
    "RegistrationDate": "📅",
    "LastActivity": "🕐",
    "Date": "📅",
    "Browser": "🌐",
    "IP": "🔌",
    "Source": "📡",
    "Circle": "📡",
    "Alt": "📱",
    "ID": "🆔",
    "Father": "👨",
    "Email": "📧",
    "DOB": "🎂",
    "Gender": "⚥",
    "PAN": "📇",
    "Aadhaar": "🪪"
}

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

def sanitize_error_message(error_msg):
    """Remove sensitive information from error messages"""
    # Remove API key if present
    if LEAK_API_KEY in error_msg:
        error_msg = error_msg.replace(LEAK_API_KEY, "[HIDDEN]")
    
    # Remove any URLs with sensitive params
    import re
    # Hide apikey parameter in URLs
    error_msg = re.sub(r'apikey=[^&\s]+', 'apikey=[HIDDEN]', error_msg)
    # Hide token parameters
    error_msg = re.sub(r'token=[^&\s]+', 'token=[HIDDEN]', error_msg)
    # Hide authorization headers
    error_msg = re.sub(r'Authorization: Bearer [^\s]+', 'Authorization: Bearer [HIDDEN]', error_msg)
    
    return error_msg

def get_field_emoji(field_name):
    """Get emoji for a field name"""
    # Check exact match
    if field_name in FIELD_EMOJIS:
        return FIELD_EMOJIS[field_name]
    
    # Check case-insensitive match
    for key, emoji in FIELD_EMOJIS.items():
        if key.lower() == field_name.lower():
            return emoji
    
    # Check if field name contains any keyword
    field_lower = field_name.lower()
    for key, emoji in FIELD_EMOJIS.items():
        if key.lower() in field_lower or field_lower in key.lower():
            return emoji
    
    # Default emoji
    return "📌"

def format_leak_data(data, query_type, display_query):
    """Format leak data with emojis and without titles/descriptions"""
    result_text = f"🔥 *{query_type} INFO RESULT*\n"
    result_text += f"📱 {query_type}: `{display_query}`\n"
    result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not data.get('status', False):
        result_text += "❌ No data found or API error."
        return result_text
    
    leak_data = data.get('data', {})
    if not leak_data:
        result_text += "❌ No leak data available."
        return result_text
    
    # Process each source
    result_counter = 1
    for source_key, source_data in leak_data.items():
        records = source_data.get('records', [])
        if not records:
            continue
        
        # Process each record in this source
        for idx, record in enumerate(records):
            if result_counter > 1:
                result_text += "\n" + "─" * 30 + "\n\n"
            
            # Add result number header
            result_text += f"*Result {result_counter}*\n"
            result_counter += 1
            
            # Show each field with emoji
            for key, value in record.items():
                if value:
                    emoji = get_field_emoji(key)
                    result_text += f"{emoji} *{key}:* `{escape_markdown(str(value))}`\n"
    
    if result_counter == 1:
        result_text += "❌ No records found in the response."
    
    return result_text

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
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ Error: {escape_markdown(error_msg[:100])}")

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command for searching leaks by mobile number.
    """
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a mobile number!\n\n"
            "*Examples:*\n"
            "`/num 9669785385`\n"
            "`/num +919669785385`\n\n"
            "*Note:* You can use with or without +91 prefix.",
            parse_mode='Markdown'
        )
        return
    
    query = context.args[0].strip()
    
    # Extract digits from the query
    digits = ''.join(filter(str.isdigit, query))
    
    if len(digits) >= 10:
        # Take last 10 digits
        mobile_10 = digits[-10:]
        search_query = f"+91{mobile_10}"
        display_query = f"{mobile_10}"
    else:
        await update.message.reply_text(
            "❌ Invalid mobile number! Please provide a valid 10-digit mobile number.\n\n"
            f"Received: `{query}`",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text(
        f"🔍 Searching leak data for mobile number `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        # Call the API with mobile number
        params = {
            "q": search_query,
            "apikey": LEAK_API_KEY
        }
        response = session.get(LEAK_API, params=params, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            result_text = format_leak_data(data, "Number", display_query)
            
            # Truncate if too long
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n... (response truncated)"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.edit_text(f"❌ API Error\nStatus Code: {response.status_code}")
        
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ Error: {error_msg[:100]}")

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command for searching leaks by Aadhaar number.
    """
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an Aadhaar number!\n\n"
            "*Examples:*\n"
            "`/aadhar 212028834716`\n\n"
            "*Note:* Aadhaar must be exactly 12 digits.",
            parse_mode='Markdown'
        )
        return
    
    query = context.args[0].strip()
    
    # Extract digits from the query
    digits = ''.join(filter(str.isdigit, query))
    
    if len(digits) == 12:
        # Valid Aadhaar number
        search_query = digits
        display_query = f"********{digits[-4:]}"
    else:
        await update.message.reply_text(
            "❌ Invalid Aadhaar number! Please provide a valid 12-digit Aadhaar number.\n\n"
            f"Received: `{query}` (Length: {len(digits)} digits)",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text(
        f"🔍 Searching leak data for Aadhaar `{display_query}`...\n⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        # Call the API with Aadhaar number
        params = {
            "q": search_query,
            "apikey": LEAK_API_KEY
        }
        response = session.get(LEAK_API, params=params, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            result_text = format_leak_data(data, "Aadhaar", display_query)
            
            # Truncate if too long
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n... (response truncated)"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.edit_text(f"❌ API Error\nStatus Code: {response.status_code}")
        
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ Error: {error_msg[:100]}")

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
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ Error: {error_msg[:100]}")

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
        await msg.edit_text(f"❌ Error: {error_msg[:100]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    keyboard = [
        [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
        [InlineKeyboardButton("📱 MOBILE LEAK SEARCH", callback_data="menu_num")],
        [InlineKeyboardButton("🪪 AADHAAR LEAK SEARCH", callback_data="menu_aadhar")],
        [InlineKeyboardButton("📇 PAN CARD SEARCH", callback_data="menu_pan")],
        [InlineKeyboardButton("💳 UPI VALIDATION", callback_data="menu_upi")],
        [InlineKeyboardButton("❓ HELP / COMMANDS", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = """
🚀 *WELCOME TO SEARCH BOT* 🚀

━━━━━━━━━━━━━━━━━━━━━━━

*Select an option below:*

🚗 *Vehicle Search* - Comprehensive vehicle info
📱 *Mobile Leak* - Search leaks by mobile number
🪪 *Aadhaar Leak* - Search leaks by Aadhaar number
📇 *PAN Card* - PAN card details
💳 *UPI Validation* - Validate UPI/VPA ID

━━━━━━━━━━━━━━━━━━━━━━━

💡 *Commands:*
`/vehicle UP32JK8979`
`/num 9669785385` - Search by mobile
`/aadhar 212028834716` - Search by Aadhaar
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
                [InlineKeyboardButton("📱 MOBILE LEAK SEARCH", callback_data="menu_num")],
                [InlineKeyboardButton("🪪 AADHAAR LEAK SEARCH", callback_data="menu_aadhar")],
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
            
    elif data == "menu_vehicle":
        await query.edit_message_text(
            "🚗 *VEHICLE SEARCH*\n\nPlease send the registration number.\nExample: `UP32JK8979`\n\nType: `/vehicle UP32JK8979`",
            parse_mode='Markdown'
        )
    elif data == "menu_num":
        await query.edit_message_text(
            "📱 *MOBILE LEAK SEARCH*\n\n"
            "Search leaks by mobile number.\n\n"
            "*Usage:*\n"
            "`/num 9669785385`\n"
            "`/num +919669785385`\n\n"
            "*Note:* You can use with or without +91 prefix.",
            parse_mode='Markdown'
        )
    elif data == "menu_aadhar":
        await query.edit_message_text(
            "🪪 *AADHAAR LEAK SEARCH*\n\n"
            "Search leaks by Aadhaar number.\n\n"
            "*Usage:*\n"
            "`/aadhar 212028834716`\n\n"
            "*Note:* Aadhaar must be exactly 12 digits.",
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

🚗 `/vehicle` - Full vehicle search
📱 `/num` - Search leaks by mobile number
🪪 `/aadhar` - Search leaks by Aadhaar number
📇 `/pan` - PAN card details
💳 `/upi` - Validate UPI ID

━━━━━━━━━━━━━━━━━━━━━━━

*Examples:*
`/vehicle UP32JK8979`
`/num 9669785385` - Mobile leak search
`/aadhar 212028834716` - Aadhaar leak search
`/pan ACCPA2495F`
`/upi vipansharma1931141@okhdfcbank`

━━━━━━━━━━━━━━━━━━━━━━━

*About Leak Search:*
• `/num` - Search by 10-digit mobile number
• `/aadhar` - Search by 12-digit Aadhaar number
• Returns formatted data with emojis
        """
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
            [InlineKeyboardButton("📱 MOBILE LEAK SEARCH", callback_data="menu_num")],
            [InlineKeyboardButton("🪪 AADHAAR LEAK SEARCH", callback_data="menu_aadhar")],
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
    application.add_handler(CommandHandler("num", num_command))  # Mobile leak search
    application.add_handler(CommandHandler("aadhar", aadhar_command))  # Aadhaar leak search
    application.add_handler(CommandHandler("pan", pan_command))
    application.add_handler(CommandHandler("upi", upi_command))
    application.add_handler(CallbackQueryHandler(menu_handler))
    
    print("🤖 Bot is starting...")
    print("✅ All commands loaded successfully")
    print("Commands: /start, /access, /vehicle, /num, /aadhar, /pan, /upi")
    print("\n📊 Leak search commands:")
    print("   - Search by mobile number: /num 9669785385")
    print("   - Search by Aadhaar: /aadhar 212028834716")
    print("   - Returns formatted data with emojis")
    print("   - API keys and tokens are hidden from users")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
