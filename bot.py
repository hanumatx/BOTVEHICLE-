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
VEHICLE_API = "https://chuchirandiki.vercel.app/api/vehicle"
LEAKOSINT_API = "https://raxxosint.onrender.com/leakosint"
LEAKOSINT_KEY = "LOS-419781895057E3B0"
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

# Field name mappings for API response
FIELD_EMOJIS = {
    "NAME": "👤",
    "fname": "👨‍👦",
    "ADDRESS": "📍",
    "MOBILE": "📞",
    "alt": "📱",
    "circle": "📡",
    "id": "🪪",
    "email": "📧",
    "icic": "🏦",
    "msid": "📱",
    "Phone": "📞",
    "Phone2": "📱",
    "Phone3": "📱",
    "Phone4": "📱",
    "Phone5": "📱",
    "Phone6": "📱",
    "Phone7": "📱",
    "Phone8": "📱",
    "FullName": "👤",
    "FatherName": "👨‍👦",
    "Adres": "📍",
    "Adres2": "📍",
    "Adres3": "📍",
    "DocumentNumber": "🪪",
    "Email": "📧",
    "Region": "📡",
    "City": "🏙️",
    "State": "🗺️",
    "PostalCode": "📮",
    "Provider": "📡",
    "MobileOperator": "📡",
    "DateOfBirth": "🎂",
    "Company": "🏢",
    "Category": "📋",
    "Type": "📋",
    "Country": "🌍",
    "IP": "🌐",
    "RegistrationDate": "📅",
    "TheDateOfTheEntrance": "📅",
    "Name": "👤",
    "Surname": "👤",
    "Nick": "👤",
    "Login": "🔑",
    "Titul": "👤",
    "EncryptedPassword": "🔒",
    "CreditsInappPoints": "⭐",
    "PinCode": "📮",
    "Email2": "📧",
    "IndianState": "🗺️",
    "MobilePhone": "📞"
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

def generate_random_icic():
    """Generate random ICIC code (alphanumeric, 11 characters)"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))

def generate_random_msid():
    """Generate random MSID (numeric, 15 digits)"""
    return ''.join(str(random.randint(0, 9)) for _ in range(15))

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
    if LEAKOSINT_KEY in error_msg:
        error_msg = error_msg.replace(LEAKOSINT_KEY, "[HIDDEN]")
    
    api_patterns = [
        r'https://chuchirandiki\.vercel\.app[^\s]*',
        r'https://api\.spinny\.com[^\s]*',
        r'https://api\.truebalance\.cc[^\s]*',
        r'https://raxxosint\.onrender\.com[^\s]*',
    ]
    for pattern in api_patterns:
        error_msg = re.sub(pattern, '[API_ENDPOINT]', error_msg)
    
    error_msg = re.sub(r'key=[^&\s]+', 'key=[HIDDEN]', error_msg)
    error_msg = re.sub(r'token=[^&\s]+', 'token=[HIDDEN]', error_msg)
    error_msg = re.sub(r'Authorization: Bearer [^\s]+', 'Authorization: Bearer [HIDDEN]', error_msg)
    
    return error_msg

def get_field_emoji(field_name):
    if field_name in FIELD_EMOJIS:
        return FIELD_EMOJIS[field_name]
    return "📌"

def format_vehicle_data(data, registration_number):
    result_text = f"🚗 *VEHICLE DETAILS*\n"
    result_text += f"🔢 *Number:* `{registration_number}`\n"
    result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not data or not data.get('success', False):
        result_text += "❌ No vehicle data found or an error occurred."
        return result_text

    vehicle_info = data.get('data', {})
    if not vehicle_info:
        result_text += "❌ No vehicle data available in the response."
        return result_text

    result_text += f"📋 *REGISTRATION & BASIC INFO*\n"
    result_text += f"├ Registration Date: `{escape_markdown(vehicle_info.get('registration_date', 'N/A'))}`\n"
    result_text += f"├ Registration Year: `{escape_markdown(vehicle_info.get('registration_year', 'N/A'))}`\n"
    result_text += f"├ Registration Month: `{escape_markdown(vehicle_info.get('registration_month', 'N/A'))}`\n"
    result_text += f"├ Registration Address: `{escape_markdown(vehicle_info.get('registration_address', 'N/A'))}`\n"
    result_text += f"├ Source: `{escape_markdown(vehicle_info.get('source', 'N/A'))}`\n"
    result_text += f"└ Asset Type: `{escape_markdown(vehicle_info.get('asset_type', 'N/A'))}`\n\n"

    result_text += f"⚙️ *VEHICLE SPECIFICATIONS*\n"
    result_text += f"├ Make: `{escape_markdown(vehicle_info.get('make_name', 'N/A'))}`\n"
    result_text += f"├ Make (Full): `{escape_markdown(vehicle_info.get('make_name2', 'N/A'))}`\n"
    result_text += f"├ Model: `{escape_markdown(vehicle_info.get('model_name', 'N/A'))}`\n"
    result_text += f"├ Model (Full): `{escape_markdown(vehicle_info.get('model_name2', 'N/A'))}`\n"
    result_text += f"├ Make & Model: `{escape_markdown(vehicle_info.get('make_model', 'N/A'))}`\n"
    result_text += f"├ Fuel Type: `{escape_markdown(vehicle_info.get('fuel_type', 'N/A'))}`\n"
    result_text += f"├ Vehicle Color: `{escape_markdown(vehicle_info.get('vehicle_color', 'N/A'))}`\n"
    result_text += f"├ Vehicle Type: `{escape_markdown(vehicle_info.get('vehicle_type', 'N/A'))}`\n"
    result_text += f"├ Vehicle Type V2: `{escape_markdown(vehicle_info.get('vehicle_type_v2', 'N/A'))}`\n"
    result_text += f"├ Chassis Number: `{escape_markdown(vehicle_info.get('chassis_number', 'N/A'))}`\n"
    result_text += f"├ Engine Number: `{escape_markdown(vehicle_info.get('engine_number', 'N/A'))}`\n"
    result_text += f"└ Commercial: {'✅ Yes' if vehicle_info.get('is_commercial') else '❌ No'}\n\n"

    result_text += f"📍 *ADDRESS INFORMATION*\n"
    if vehicle_info.get('permanent_address'):
        result_text += f"├ Permanent Address: `{escape_markdown(vehicle_info.get('permanent_address'))}`\n"
    if vehicle_info.get('present_address'):
        result_text += f"└ Present Address: `{escape_markdown(vehicle_info.get('present_address'))}`\n"
    result_text += "\n"

    if vehicle_info.get('previous_insurer'):
        result_text += f"🛡️ *INSURANCE INFORMATION*\n"
        result_text += f"├ Previous Insurer: `{escape_markdown(vehicle_info.get('previous_insurer', 'N/A'))}`\n"
        result_text += f"├ Policy Expiry Date: `{escape_markdown(vehicle_info.get('previous_policy_expiry_date', 'N/A'))}`\n"
        result_text += f"└ Policy Expired: {'✅ Yes' if vehicle_info.get('previous_policy_expired') else '❌ No'}\n\n"

    result_text += f"📌 *ADDITIONAL DETAILS*\n"
    result_text += f"├ Asset Number: `{escape_markdown(vehicle_info.get('asset_number', 'N/A'))}`\n"
    if vehicle_info.get('variant_id'):
        variant_ids = ', '.join(str(v) for v in vehicle_info.get('variant_id', []))
        result_text += f"└ Variant IDs: `{escape_markdown(variant_ids)}`\n"

    return result_text

def format_leakosint_data(data, query, search_type="number"):
    """
    Format data from the Leakosint API with emojis
    Shows all data from all sources without developer name and source title
    """
    if search_type == "number":
        result_text = f"🔥 *Number Info Result*\n"
        result_text += f"📱 Number: `{query}`\n"
    else:
        result_text = f"🔥 *Aadhaar Info Result*\n"
        result_text += f"🪪 Aadhaar: `{query}`\n"
    
    result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not data:
        result_text += "❌ No information found for this query."
        return result_text
    
    # Check if we have data dictionary with sources
    if isinstance(data, dict):
        # Get all sources except we'll skip the developer field
        sources = {k: v for k, v in data.items() if k not in ['developer', 'status', 'success', 'status_code', 'http_status', 'query']}
        
        record_count = 0
        for source_name, source_data in sources.items():
            if not isinstance(source_data, dict):
                continue
                
            # Skip source title and description, just get records
            records = source_data.get('records', [])
            if not records:
                continue
                
            for record in records:
                record_count += 1
                if record_count == 1:
                    # No source header - just show data
                    result_text += f"📂 *Record #{record_count}*\n"
                else:
                    result_text += f"\n📂 *Record #{record_count}*\n"
                result_text += "─────────────────\n"
                
                # Define display names for fields
                field_display = {
                    "FullName": "Full Name",
                    "Name": "Name",
                    "Surname": "Surname",
                    "FatherName": "Father's Name",
                    "Phone": "Phone Number",
                    "Phone2": "Phone 2",
                    "Phone3": "Phone 3",
                    "Phone4": "Phone 4",
                    "Phone5": "Phone 5",
                    "Phone6": "Phone 6",
                    "Phone7": "Phone 7",
                    "Phone8": "Phone 8",
                    "MobilePhone": "Mobile Phone",
                    "Email": "Email Address",
                    "Email2": "Email 2",
                    "Adres": "Address",
                    "Adres2": "Address 2",
                    "Adres3": "Address 3",
                    "DocumentNumber": "Document Number",
                    "Region": "Region",
                    "City": "City",
                    "State": "State",
                    "IndianState": "State",
                    "Country": "Country",
                    "PostalCode": "Postal Code",
                    "Provider": "Provider",
                    "MobileOperator": "Mobile Operator",
                    "DateOfBirth": "Date of Birth",
                    "Company": "Company",
                    "Category": "Category",
                    "Type": "Type",
                    "IP": "IP Address",
                    "RegistrationDate": "Registration Date",
                    "TheDateOfTheEntrance": "Last Login Date",
                    "Nick": "Nickname",
                    "Login": "Login ID",
                    "Titul": "Title",
                    "EncryptedPassword": "Encrypted Password",
                    "CreditsInappPoints": "Points/Balance",
                    "PinCode": "PIN Code",
                    "Stat": "State"
                }
                
                # Define field order for better readability
                field_order = ["FullName", "Name", "Surname", "FatherName", "Phone", "Phone2", "Phone3", "Phone4", "Phone5", "Phone6", "Phone7", "Phone8", "MobilePhone", "Email", "Email2", "Adres", "Adres2", "Adres3", "DocumentNumber", "Region", "City", "State", "IndianState", "Country", "PostalCode", "Provider", "MobileOperator", "DateOfBirth", "Company", "Category", "Type", "IP", "RegistrationDate", "TheDateOfTheEntrance", "Nick", "Login", "Titul", "EncryptedPassword", "CreditsInappPoints", "PinCode", "Stat"]
                
                # Show fields in preferred order
                for field in field_order:
                    if field in record and record[field] and str(record[field]).strip() and str(record[field]).lower() != 'null':
                        emoji = get_field_emoji(field)
                        display_value = str(record[field])
                        
                        # Handle Aadhaar/Document masking for display if needed
                        if field in ["DocumentNumber", "id"] and len(display_value) >= 12:
                            # Don't mask completely, show full if available
                            pass
                        
                        display_field = field_display.get(field, field.replace('_', ' ').title())
                        result_text += f"{emoji} *{display_field}:* `{escape_markdown(display_value)}`\n"
                
                # Show any remaining fields
                for key, value in record.items():
                    if key not in field_order and key not in ['source', 'title', 'description'] and value and str(value).strip() and str(value).lower() != 'null':
                        emoji = get_field_emoji(key)
                        display_field = key.replace('_', ' ').title()
                        result_text += f"{emoji} *{display_field}:* `{escape_markdown(str(value))}`\n"
        
        if record_count == 0:
            result_text += "❌ No records found in any source."
    
    elif isinstance(data, list):
        # Handle list of records directly
        for idx, record in enumerate(data, 1):
            if idx == 1:
                result_text += f"📂 *Record #{idx}*\n"
            else:
                result_text += f"\n📂 *Record #{idx}*\n"
            result_text += "─────────────────\n"
            
            for key, value in record.items():
                if value and str(value).strip() and str(value).lower() != 'null':
                    emoji = get_field_emoji(key)
                    display_field = key.replace('_', ' ').title()
                    result_text += f"{emoji} *{display_field}:* `{escape_markdown(str(value))}`\n"
    
    else:
        result_text += "❌ Unexpected response format from API."
    
    return result_text.rstrip()

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
        await update.message.reply_text("❌ Please provide a registration number!\n\nExample: `/vehicle MH47BG7036`", parse_mode='Markdown')
        return
    
    registration_number = context.args[0].upper().strip()
    msg = await update.message.reply_text(f"🔍 Fetching details for vehicle `{registration_number}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    try:
        params = {"reg_no": registration_number}
        response = session.get(VEHICLE_API, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data'):
                result_text = format_vehicle_data(data, registration_number)
            else:
                result_text = f"🚗 *VEHICLE DETAILS*\n"
                result_text += f"🔢 *Number:* `{registration_number}`\n"
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result_text += "❌ No vehicle data found for this registration number."
            
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n... (response truncated)"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.edit_text(f"❌ Failed to fetch vehicle details. Please try again later.")
        
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ An error occurred while fetching data. Please try again later.")

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a mobile number!\n\n"
            "*Examples:*\n"
            "`/num 8810590661`\n"
            "`/num +918810590661`\n\n"
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
        params = {
            "key": LEAKOSINT_KEY,
            "quiry": f"+91{number}"
        }
        response = session.get(LEAKOSINT_API, params=params, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data'):
                result_text = format_leakosint_data(data.get('data'), display_query, "number")
            else:
                result_text = f"🔥 *Number Info Result*\n"
                result_text += f"📱 Number: `{display_query}`\n"
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result_text += "❌ No information found for this number."
            
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n... (response truncated)"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.edit_text(f"❌ Failed to fetch number details. Status: {response.status_code}")
        
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        logger.error(f"Error in num_command: {error_msg}")
        await msg.edit_text(f"❌ An error occurred while fetching data. Please try again later.")

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an Aadhaar number!\n\n"
            "*Examples:*\n"
            "`/aadhar 691631435425`\n\n"
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
            "key": LEAKOSINT_KEY,
            "quiry": aadhaar_number
        }
        response = session.get(LEAKOSINT_API, params=params, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data'):
                result_text = format_leakosint_data(data.get('data'), display_query, "aadhar")
            else:
                result_text = f"🔥 *Aadhaar Info Result*\n"
                result_text += f"🪪 Aadhaar: `{display_query}`\n"
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result_text += "❌ No information found for this Aadhaar number."
            
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n... (response truncated)"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.edit_text(f"❌ Failed to fetch Aadhaar details. Status: {response.status_code}")
        
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        logger.error(f"Error in aadhar_command: {error_msg}")
        await msg.edit_text(f"❌ An error occurred while fetching data. Please try again later.")

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

🚗 *Vehicle Search* - Comprehensive vehicle info
📱 *Mobile Search* - Mobile number details
🪪 *Aadhaar Search* - Aadhaar number details
📇 *PAN Card* - PAN card details
💳 *UPI Validation* - Validate UPI/VPA ID

━━━━━━━━━━━━━━━━━━━━━━━

💡 *Commands:*
`/vehicle MH47BG7036`
`/num 8810590661` - Mobile details (use +91)
`/aadhar 691631435425` - Aadhaar details
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
            await query.answer("❌ You still haven't joined the channel!", show_alert=True)
            
    elif data == "menu_vehicle":
        await query.edit_message_text(
            "🚗 *VEHICLE SEARCH*\n\nPlease send the registration number.\nExample: `MH47BG7036`\n\nType: `/vehicle MH47BG7036`",
            parse_mode='Markdown'
        )
    elif data == "menu_num":
        await query.edit_message_text(
            "📱 *MOBILE SEARCH*\n\n"
            "Search details for any mobile number.\n\n"
            "*Usage:*\n"
            "`/num 8810590661`\n"
            "`/num +918810590661`\n\n"
            "*Returns comprehensive data from multiple sources:*\n"
            "• Full Name & Father's Name\n"
            "• Phone numbers (up to 8)\n"
            "• Addresses & Email\n"
            "• Document Numbers\n"
            "• Region & City\n"
            "• Provider & Operator\n"
            "• Company & Category\n"
            "• Date of Birth & More",
            parse_mode='Markdown'
        )
    elif data == "menu_aadhar":
        await query.edit_message_text(
            "🪪 *AADHAAR SEARCH*\n\n"
            "Search details by Aadhaar number.\n\n"
            "*Usage:*\n"
            "`/aadhar 691631435425`\n\n"
            "*Note:* Aadhaar must be exactly 12 digits.\n\n"
            "*Returns comprehensive data from multiple sources:*\n"
            "• Full Name & Father's Name\n"
            "• Phone numbers (up to 8)\n"
            "• Addresses & Email\n"
            "• Document Numbers\n"
            "• Region & City\n"
            "• Provider & Operator\n"
            "• Company & Category\n"
            "• Date of Birth & More",
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
📱 `/num` - Mobile number details (Leakosint API)
🪪 `/aadhar` - Aadhaar number details (Leakosint API)
📇 `/pan` - PAN card details
💳 `/upi` - Validate UPI ID

━━━━━━━━━━━━━━━━━━━━━━━

*Examples:*
`/vehicle MH47BG7036`
`/num +919873534030` - Mobile details
`/aadhar 691631435425` - Aadhaar details
`/pan ACCPA2495F`
`/upi vipansharma1931141@okhdfcbank`

━━━━━━━━━━━━━━━━━━━━━━━

*About Mobile & Aadhaar Search:*
• Uses Leakosint API for comprehensive data
• Returns data from multiple sources
• Shows all records with complete details
• Fields include: Name, Father's Name, Multiple Phone Numbers, Addresses, Email, Document Numbers, Region, City, State, Provider, Company, Date of Birth, and more

*About Vehicle Search:*
• `/vehicle` - Search by registration number
• Returns: Registration Status, Vehicle Specs, Address, Insurance, Additional Details

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
    print("\n🚗 Vehicle Search:")
    print("   - API: https://chuchirandiki.vercel.app/api/vehicle?reg_no=XXXXXXXXXX")
    print("   - Usage: /vehicle MH47BG7036")
    print("\n📱 Mobile Search:")
    print("   - API: https://raxxosint.onrender.com/leakosint?key=LOS-419781895057E3B0&quiry=+919873534030")
    print("   - Usage: /num +919873534030")
    print("   - Returns: Complete data from all sources")
    print("\n🪪 Aadhaar Search:")
    print("   - API: https://raxxosint.onrender.com/leakosint?key=LOS-419781895057E3B0&quiry=691631435425")
    print("   - Usage: /aadhar 691631435425")
    print("   - Returns: Complete data from all sources")
    print("\n📇 PAN Search:")
    print("   - Usage: /pan ACCPA2495F")
    print("\n💳 UPI Validation:")
    print("   - Usage: /upi vipansharma1931141@okhdfcbank")
    print("\n🔒 All API endpoints and keys are hidden from users")
    print("\n✅ Bot is ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
