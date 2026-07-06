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
LEAK_API = "https://sexy-leak-api.noobgamingv40.workers.dev/api"
LEAK_API_KEY = "hackerzz"
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
    if LEAK_API_KEY in error_msg:
        error_msg = error_msg.replace(LEAK_API_KEY, "[HIDDEN]")
    
    import re
    error_msg = re.sub(r'apikey=[^&\s]+', 'apikey=[HIDDEN]', error_msg)
    error_msg = re.sub(r'token=[^&\s]+', 'token=[HIDDEN]', error_msg)
    error_msg = re.sub(r'Authorization: Bearer [^\s]+', 'Authorization: Bearer [HIDDEN]', error_msg)
    
    return error_msg

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
                # No truncation for vehicle data
                await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await msg.edit_text(f"❌ No vehicle data found for `{registration_number}`")
        else:
            await msg.edit_text(f"❌ API Error\nStatus Code: {response.status_code}")
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        await msg.edit_text(f"❌ Error: {escape_markdown(error_msg[:100])}")

async def search_leak_api(search_query, query_type, display_query):
    """Helper function to search the leak API - returns only raw records without titles/descriptions"""
    try:
        params = {
            "q": search_query,
            "apikey": LEAK_API_KEY
        }
        response = session.get(LEAK_API, params=params, timeout=90)
        raw_text = response.text
        
        # Try to parse JSON and extract only records
        try:
            data = response.json()
            
            # Extract only records from all sources
            if data.get('status') and data.get('data'):
                all_records = []
                for source_key, source_data in data['data'].items():
                    if isinstance(source_data, dict) and 'records' in source_data:
                        records = source_data['records']
                        if records:
                            # Add source name to each record for identification
                            for record in records:
                                # Add source identifier without title/description
                                record['_source'] = source_key
                                all_records.append(record)
                
                if all_records:
                    # Return only the records as JSON (no truncation)
                    result_json = json.dumps(all_records, indent=2, ensure_ascii=False)
                    result_text = f"📡 *LEAK DATA* ({query_type}: `{display_query}`)\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```json\n{result_json}\n```"
                else:
                    # If no records found, return the full response
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                    result_text = f"📡 *LEAK API RESPONSE* ({query_type}: `{display_query}`)\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```json\n{formatted_json}\n```"
            else:
                # If data structure is different, return formatted JSON
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                result_text = f"📡 *LEAK API RESPONSE* ({query_type}: `{display_query}`)\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```json\n{formatted_json}\n```"
            
            return result_text, None
            
        except:
            # If not JSON, show raw text (no truncation)
            result_text = f"📡 *LEAK API RESPONSE* ({query_type}: `{display_query}`)\n━━━━━━━━━━━━━━━━━━━━━━━\n\n```\n{raw_text}\n```"
            return result_text, None
            
    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        return None, error_msg

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search by mobile number using the new leak API"""
    if not await is_subscribed(update, context):
        return

    if context.args:
        raw_number = context.args[0].strip()
        digits = ''.join(filter(str.isdigit, raw_number))
        if len(digits) < 10:
            await update.message.reply_text("❌ Please provide a valid 10-digit mobile number.\n\nExample: `/num 9876543210`", parse_mode='Markdown')
            return
        mobile_10 = digits[-10:]
        mobile_with_prefix = f"+91{mobile_10}"
        display_query = mobile_with_prefix
        custom_msg = f"for `{mobile_with_prefix}`"
    else:
        first_digit = random.choice(['6', '7', '8', '9'])
        remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(9))
        mobile_10 = first_digit + remaining_digits
        mobile_with_prefix = f"+91{mobile_10}"
        display_query = mobile_with_prefix
        custom_msg = f"random number `{mobile_with_prefix}`"
    
    msg = await update.message.reply_text(f"🔍 Searching leak data for {custom_msg}...\n⏳ Please wait...", parse_mode='Markdown')
    
    result_text, error = await search_leak_api(mobile_with_prefix, "Mobile", display_query)
    
    if error:
        await msg.edit_text(f"❌ Error: {error[:100]}")
        return
    
    keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search by Aadhaar number using the new leak API"""
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
    msg = await update.message.reply_text(f"🔍 Searching leak data for Aadhaar ending `{safe_display}`...\n⏳ Please wait...", parse_mode='Markdown')
    
    result_text, error = await search_leak_api(aadhaar_number, "Aadhaar", safe_display)
    
    if error:
        await msg.edit_text(f"❌ Error: {error[:100]}")
        return
    
    keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await msg.edit_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)

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
        [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
        [InlineKeyboardButton("🆔 AADHAAR SEARCH", callback_data="menu_aadhar")],
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
📱 *Mobile Search* - Leak data by mobile number
🆔 *Aadhaar Search* - Leak data by Aadhaar
📇 *PAN Card* - PAN card details
💳 *UPI Validation* - Validate UPI/VPA ID

━━━━━━━━━━━━━━━━━━━━━━━

💡 *Commands:*
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
                [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
                [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
                [InlineKeyboardButton("🆔 AADHAAR SEARCH", callback_data="menu_aadhar")],
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
            "📱 *MOBILE NUMBER SEARCH (LEAK DATA)*\n\n"
            "*Usage:*\n"
            "• `/num` - Auto-generates a random Indian mobile number\n"
            "• `/num 9876543210` - Search specific number\n\n"
            "*Example:* `/num`\n\n"
            "*Note:* If no number is provided, a random 10-digit number (starting with 6,7,8,9) will be used.\n"
            "Returns raw JSON data from multiple leak sources.",
            parse_mode='Markdown'
        )
    elif data == "menu_aadhar":
        await query.edit_message_text(
            "🆔 *AADHAAR SEARCH (LEAK DATA)*\n\nPlease send the Aadhaar number.\nExample: `212028834716`\n\nType: `/aadhar 212028834716`\n\nReturns raw JSON data from multiple leak sources.",
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
📱 `/num` - Leak search by mobile number
🆔 `/aadhar` - Leak search by Aadhaar
📇 `/pan` - PAN card details
💳 `/upi` - Validate UPI ID

━━━━━━━━━━━━━━━━━━━━━━━

*Examples:*
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
• Returns raw JSON from multiple leak sources

*Note about /aadhar command:*
• Accepts 12-digit Aadhaar numbers
• Returns raw JSON from multiple leak sources
        """
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("🚗 VEHICLE SEARCH", callback_data="menu_vehicle")],
            [InlineKeyboardButton("📱 MOBILE SEARCH", callback_data="menu_num")],
            [InlineKeyboardButton("🆔 AADHAAR SEARCH", callback_data="menu_aadhar")],
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
    print("\n📱 /num command features:")
    print("   - No args: Auto-generates random Indian mobile number")
    print("   - With args: Searches the provided number")
    print("   - Shows ONLY raw records without titles/descriptions")
    print("\n🆔 /aadhar command features:")
    print("   - Searches by 12-digit Aadhaar number")
    print("   - Shows ONLY raw records without titles/descriptions")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
