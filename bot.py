import os
import io
import json
import time
import asyncio
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from generator import generate_receipt_image, download_fonts

# ─── Configuration ───
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    if os.path.exists("token.txt"):
        TOKEN = open("token.txt").read().strip()
    else:
        TOKEN = "YOUR_BOT_TOKEN_HERE"

ADMIN_ID = 7837935671

# Global state
admin_states = {}  # user_id -> string (awaiting input state)
user_settings = {}  # chat_id -> dict
active_tasks = {}  # chat_id -> asyncio.Task

# ─── Global Config File ───
GLOBAL_CONFIG_PATH = "styles/global_config.json"

def get_global_config():
    os.makedirs("styles", exist_ok=True)
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    default_config = {
        "channels": ["@ai_receipt_channel"],
        "invite_links": ["https://t.me/ai_receipt_channel"],
        "cooling_period": 30,
        "referral_reward": 5   # Default 5 bills per successful refer
    }
    save_global_config(default_config)
    return default_config

def save_global_config(config):
    os.makedirs("styles", exist_ok=True)
    try:
        with open(GLOBAL_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Failed to save global config: {e}")

# ─── User Settings ───
DEFAULT_SETTINGS = {
    "credits": 0,              # Users start with 0 bills initially
    "joined_channel": False,   # Set to True once they join channels and claim 3 free bills
    "last_gen_time": 0,        # Cooldown check
    "referred_by": "",         # Referrer ID
    "referral_rewarded": False, # Prevent double rewarding
    "referrals_count": 0       # Total successful referrals
}

def get_user_settings(chat_id):
    chat_str = str(chat_id)
    if chat_str not in user_settings:
        settings_path = f"styles/{chat_str}_settings.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    user_settings[chat_str] = json.load(f)
            except Exception:
                user_settings[chat_str] = DEFAULT_SETTINGS.copy()
        else:
            user_settings[chat_str] = DEFAULT_SETTINGS.copy()
            
    # Ensure default fields are present
    for k, v in DEFAULT_SETTINGS.items():
        if k not in user_settings[chat_str]:
            user_settings[chat_str][k] = v
            
    return user_settings[chat_str]

def save_user_settings(chat_id, settings):
    chat_str = str(chat_id)
    os.makedirs("styles", exist_ok=True)
    settings_path = f"styles/{chat_str}_settings.json"
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Failed to save settings for {chat_str}: {e}")

# ─── Keep-Alive HTTP Server ───

class RenderHealthCheckHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Receipt Generator Telegram Bot is Active and Healthy!")
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RenderHealthCheckHandler)
    print(f"Health check server listening on port {port}...")
    server.serve_forever()

# ─── Access Control: Channel check, Cooldown, and Referral System ───

async def check_channel_memberships(bot, user_id):
    """Checks if a user is a member of ALL required channels."""
    if user_id == ADMIN_ID:
        return True, None
        
    config = get_global_config()
    channels = config.get("channels", ["@ai_receipt_channel"])
    
    for channel in channels:
        if not channel:
            continue
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["creator", "administrator", "member"]:
                return False, channel
        except Exception as e:
            print(f"Channel membership check failed for {channel}: {e}")
            if "Chat not found" in str(e) or "chat not found" in str(e) or "bot is not a member" in str(e):
                print(f"WARNING: Channel {channel} not found or bot is not admin. Bypassing check for testing.")
                continue
            return False, channel
    return True, None

async def enforce_membership_and_credits(chat_id, context, settings, consume_credit=False):
    """
    Checks channel memberships, cooldowns, and credit balance.
    Admin gets complete bypass.
    """
    if chat_id == ADMIN_ID:
        return True

    config = get_global_config()
    channels = config.get("channels", ["@ai_receipt_channel"])
    invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
    
    # 1. Enforce Channel Memberships
    is_member, blocked_channel = await check_channel_memberships(context.bot, chat_id)
    
    if not is_member:
        # User left a channel! Deduct 3 free bills join reward
        if settings.get("joined_channel", False):
            settings["joined_channel"] = False
            settings["credits"] = max(0, settings.get("credits", 0) - 3)
            save_user_settings(chat_id, settings)
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ **Dhyan dein**: Aapne required channel leave kiya hai! Aapke balance se **3 free bills** deduct kar diye gaye hain."
            )
            
        # Display join prompt
        keyboard = []
        for i, channel in enumerate(channels):
            link = invite_links[i] if i < len(invite_links) else f"https://t.me/{channel.replace('@', '')}"
            keyboard.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
            
        keyboard.append([InlineKeyboardButton("🔄 Verify Membership & Unlock 3 Bills", callback_data="btn_verify_join")])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ **Access Restricted!**\n\n"
                f"Bot use karne ke liye aapko hamare sabhi required channels join karne honge.\n\n"
                f"Niche diye gaye channels ko join karein aur verify button par click karein!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return False
        
    # User is in all channels. Reward if not marked.
    if not settings.get("joined_channel", False):
        settings["joined_channel"] = True
        settings["credits"] = settings.get("credits", 0) + 3  # Join channel awards exactly 3 bills
        save_user_settings(chat_id, settings)
        
        # Handle referral rewards
        referred_by = settings.get("referred_by", "")
        if referred_by and not settings.get("referral_rewarded", False):
            settings["referral_rewarded"] = True
            save_user_settings(chat_id, settings)
            
            # Award config amount to referrer
            referral_reward = config.get("referral_reward", 5)
            ref_settings = get_user_settings(referred_by)
            ref_settings["credits"] = ref_settings.get("credits", 0) + referral_reward
            ref_settings["referrals_count"] = ref_settings.get("referrals_count", 0) + 1
            save_user_settings(referred_by, ref_settings)
            
            try:
                await context.bot.send_message(
                    chat_id=referred_by,
                    text=f"🎉 **Referral Success!**\n\nAapke referral link se kisi ne bot join kiya hai. Aapko **+{referral_reward} free bills** mil gaye hain!"
                )
            except Exception:
                pass
                
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 **Channels join karne ke liye dhanyawad!**\nAapke account me **3 free bills** add kar diye gaye hain."
        )

    # 2. Check Cooldown (Only when consuming credits for generation)
    if consume_credit:
        last_gen = settings.get("last_gen_time", 0)
        cooldown = config.get("cooling_period", 30)
        elapsed = time.time() - last_gen
        
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ **Cooldown Active!**\n\nKripya **{remaining} seconds** wait karein agla bill generate karne se pehle."
            )
            return False

    # 3. Check Credit Balance
    credits = settings.get("credits", 0)
    if consume_credit:
        if credits < 1:
            ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"❌ **Bills khatam ho gaye hain!**\n\nAapke pass abhi 0 bills bache hain.\n\n"
                    f"🔗 **Refer & Earn program**:\n"
                    f"Apne dosto ko refer karke aur free bills kamayein:\n"
                    f"`{ref_link}`"
                ),
                parse_mode="Markdown"
            )
            return False
        else:
            settings["credits"] = credits - 1
            settings["last_gen_time"] = time.time()
            save_user_settings(chat_id, settings)
            
    return True

# ─── Receipt Rendering Helper ───

async def render_and_send_receipt(chat_id, context, settings):
    """Runs PIL receipt rendering in a background thread and sends it as a photo."""
    img, data = await asyncio.to_thread(generate_receipt_image)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    
    credits = settings.get("credits", 0)
    
    shop_name = data["store_name"]
    address = data["store_addr"]
    rounded_total = float(round(data["total"]))
    
    caption = (
        f"🧾 **Bill generated ho gaya hai!**\n\n"
        f"🏬 **Dukan Name**: {shop_name}\n"
        f"📍 **Address**: {address}\n"
        f"💰 **Total Bill**: `₹ {rounded_total:.2f}`\n"
    )
    if chat_id != ADMIN_ID:
        caption += f"\n💰 **Aapka Balance**: `{credits} bills`"
    else:
        caption += "\n👑 Admin Unlimited Mode Active."
        
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=buf,
        caption=caption,
        parse_mode="Markdown",
        filename="bill.png"
    )

# ─── Admin Continuous Auto-Stream Task ───

async def admin_stream_task(chat_id, context, settings):
    """Continuous stream loop for Admin only (unlimited bills)."""
    count = 1
    try:
        while True:
            await render_and_send_receipt(chat_id, context, settings)
            count += 1
            await asyncio.sleep(2.5)  # Send a new bill every 2.5 seconds
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Admin stream error: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"🛑 Auto-Stream stop ho gaya: {e}")
    finally:
        active_tasks.pop(chat_id, None)

# ─── Reply Keyboards ───

def make_main_keyboard(chat_id):
    keyboard = []
    
    # 1. Main Action Row
    keyboard.append(["⚡ Generate Bill"])
    
    # 2. Stats & Help Row
    keyboard.append(["💰 My Balance", "👥 Refer & Earn"])
    
    # 3. Support & Help
    row3 = ["❓ Support & Help"]
    if chat_id == ADMIN_ID:
        row3.insert(0, "👑 Admin Panel")
    keyboard.append(row3)
    
    # 4. Admin stream controls
    if chat_id == ADMIN_ID:
        is_streaming = chat_id in active_tasks
        if is_streaming:
            keyboard.append(["⏹ Stop Auto-Stream"])
        else:
            keyboard.append(["▶️ Start Auto-Stream"])
            
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ─── Broadcast Execution (Media/Copy Cloner) ───

async def execute_broadcast(message_to_copy, context):
    """Broadcasts a exact copy of ANY message (text, media, buttons) to all active users."""
    admin_id = message_to_copy.chat.id
    status_message = await context.bot.send_message(
        chat_id=admin_id,
        text="📢 **Broadcast shuru ho raha hai...**\nSabhhi active users ko message send kiya ja raha hai."
    )
    
    count = 0
    failed = 0
    
    os.makedirs("styles", exist_ok=True)
    users = []
    for filename in os.listdir("styles"):
        if filename.endswith("_settings.json"):
            parts = filename.split("_")
            if len(parts) >= 2:
                target_id = parts[0]
                if target_id != "global":
                    users.append(target_id)
                    
    total = len(users)
    
    for i, target_id in enumerate(users):
        try:
            # Clones formatting, captions, inline buttons, photos, videos, etc.
            await context.bot.copy_message(
                chat_id=target_id,
                from_chat_id=admin_id,
                message_id=message_to_copy.message_id
            )
            count += 1
        except Exception as e:
            print(f"Failed to copy broadcast to {target_id}: {e}")
            failed += 1
            
        # Update progress indicator every 10 users
        if (i + 1) % 10 == 0 or i + 1 == total:
            try:
                await status_message.edit_text(
                    f"📢 **Broadcast Progress Update**:\n\n"
                    f"• Bheja gaya: `{i+1} / {total}` users ko\n"
                    f"• Success: `{count}`\n"
                    f"• Failed/Blocked: `{failed}`"
                )
            except Exception:
                pass
            # Avoid API flood
            await asyncio.sleep(0.5)
            
    await context.bot.send_message(
        chat_id=admin_id,
        text=(
            f"✅ **Broadcast Safaltapurvak Poora Hua!**\n\n"
            f"• Safal send: `{count}` users ko\n"
            f"• Failed/Blocked: `{failed}` users"
        )
    )

# ─── Command Handlers ───

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if referred
    settings = get_user_settings(chat_id)
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].split("_")[1])
            if not settings.get("referred_by") and referrer_id != user_id:
                settings["referred_by"] = str(referrer_id)
                save_user_settings(chat_id, settings)
        except Exception as e:
            print(f"Error parsing referral: {e}")
            
    # Enforce channel memberships immediately for standard users
    if user_id != ADMIN_ID:
        is_member, _ = await check_channel_memberships(context.bot, chat_id)
        if not is_member:
            await enforce_membership_and_credits(chat_id, context, settings, consume_credit=False)
            return
        else:
            # Auto-credit 3 bills if they are already joined
            if not settings.get("joined_channel", False):
                settings["joined_channel"] = True
                settings["credits"] = settings.get("credits", 0) + 3
                save_user_settings(chat_id, settings)
                
                # Reward referrer
                referred_by = settings.get("referred_by", "")
                if referred_by and not settings.get("referral_rewarded", False):
                    settings["referral_rewarded"] = True
                    save_user_settings(chat_id, settings)
                    
                    config = get_global_config()
                    referral_reward = config.get("referral_reward", 5)
                    ref_settings = get_user_settings(referred_by)
                    ref_settings["credits"] = ref_settings.get("credits", 0) + referral_reward
                    ref_settings["referrals_count"] = ref_settings.get("referrals_count", 0) + 1
                    save_user_settings(referred_by, ref_settings)
                    try:
                        await context.bot.send_message(
                            chat_id=referred_by,
                            text=f"🎉 **Referral Success!**\n\nAapke referral link se kisi ne bot join kiya hai. Aapko **+{referral_reward} free bills** mil gaye hain!"
                        )
                    except Exception:
                        pass
                
                await update.message.reply_text("🎉 **Membership Verified!**\nAapko **3 free bills** mil gaye hain.")

    credits = settings.get("credits", 0)
    config = get_global_config()
    cooldown = config.get("cooling_period", 30)
    ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
    
    welcome_text = (
        f"👋 **Namaste! Swagat hai aapka Indian Cafes & Hotels Bill Generator bot me!** 🧾\n\n"
        f"Yahan aap original-looking, authentic bills generate kar sakte hain.\n\n"
        f"💰 **Aapka Balance**: `{credits} bills`\n"
        f"⏱ **Cooling Period**: `{cooldown} seconds`\n\n"
        f"📢 **Note**: Naye users ko channel join karne par **3 free bills** milte hain.\n"
        f"Refer karke aap aur free bills earn kar sakte hain!"
    )
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=make_main_keyboard(chat_id),
        parse_mode="Markdown"
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
        
    config = get_global_config()
    channels = config.get("channels", ["@ai_receipt_channel"])
    invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
    cooldown = config.get("cooling_period", 30)
    referral_reward = config.get("referral_reward", 5)
    
    text = (
        "👑 **Admin Control Panel**\n\n"
        f"• **Cooling Period**: `{cooldown}s`\n"
        f"• **Referral Reward**: `{referral_reward} bills`\n"
        f"• **Required Channels**:\n"
    )
    for i, ch in enumerate(channels):
        link = invite_links[i] if i < len(invite_links) else "N/A"
        text += f"  {i+1}. `{ch}` -> [Invite Link]({link})\n"
        
    text += (
        "\n⚡ **Admin Quick Actions & Commands**:\n"
        "• `/give [user_id] [amount]` - Add bills to a user\n"
        "• `/giveall [amount]` - Add bills to all active users\n"
        "• `/setrefer [amount]` - Set referral reward amount\n"
        "• `/broadcast [message]` - Broadcast Markdown text directly\n"
    )
        
    keyboard = [
        [
            InlineKeyboardButton("⏱ Edit Cooldown", callback_data="adm_edit_cooldown"),
            InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")
        ],
        [
            InlineKeyboardButton("➕ Add Channel", callback_data="adm_add_channel"),
            InlineKeyboardButton("➖ Remove Channel", callback_data="adm_remove_channel")
        ]
    ]
    
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─── Admin Billing Credit Commands ───

async def give_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/give [user_id] [amount]`", parse_mode="Markdown")
        return
        
    try:
        target_id = context.args[0].strip()
        amount = int(context.args[1])
        
        target_settings = get_user_settings(target_id)
        target_settings["credits"] = target_settings.get("credits", 0) + amount
        save_user_settings(target_id, target_settings)
        
        await update.message.reply_text(f"✅ Successfully gave **{amount} bills** to user `{target_id}`.", parse_mode="Markdown")
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 **Reward Alert!**\n\nThe admin has credited **+{amount} bills** to your balance!"
            )
        except Exception:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Amount must be an integer.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def giveall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: `/giveall [amount]`", parse_mode="Markdown")
        return
        
    try:
        amount = int(context.args[0])
        count = 0
        
        os.makedirs("styles", exist_ok=True)
        for filename in os.listdir("styles"):
            if filename.endswith("_settings.json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    t_id = parts[0]
                    if t_id == "global":
                        continue
                    t_settings = get_user_settings(t_id)
                    t_settings["credits"] = t_settings.get("credits", 0) + amount
                    save_user_settings(t_id, t_settings)
                    count += 1
                    
        await update.message.reply_text(f"✅ Successfully gave **{amount} bills** to all **{count} active users**.", parse_mode="Markdown")
        
    except ValueError:
        await update.message.reply_text("❌ Amount must be an integer.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def setrefer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: `/setrefer [amount]`", parse_mode="Markdown")
        return
        
    try:
        amount = int(context.args[0])
        config = get_global_config()
        config["referral_reward"] = amount
        save_global_config(config)
        
        await update.message.reply_text(f"✅ Referral reward updated to **{amount} bills**.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Amount must be an integer.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ─── Callback Handler ───

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    settings = get_user_settings(chat_id)
    data = query.data
    
    # Enforce channel memberships immediately for standard users
    if user_id != ADMIN_ID and data != "btn_verify_join":
        is_member, _ = await check_channel_memberships(context.bot, chat_id)
        if not is_member:
            await enforce_membership_and_credits(chat_id, context, settings, consume_credit=False)
            return

    # --- Cancel Admin Action ---
    if data == "btn_cancel_admin":
        if user_id != ADMIN_ID:
            return
        admin_states.pop(user_id, None)
        await query.edit_message_text("❌ Action cancel kar diya gaya hai.")
        return

    # --- Admin Button Actions ---
    elif data.startswith("adm_"):
        if user_id != ADMIN_ID:
            return
            
        cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Karein", callback_data="btn_cancel_admin")]])
        
        if data == "adm_edit_cooldown":
            admin_states[user_id] = "awaiting_cooldown"
            await query.edit_message_text(
                text="⏱ **Cooling Period change karein**\n\nNaya cooling period seconds me enter karein (e.g. `60`):",
                reply_markup=cancel_markup
            )
            
        elif data == "adm_add_channel":
            admin_states[user_id] = "awaiting_add_channel"
            await query.edit_message_text(
                text=(
                    "➕ **Naya Channel add karein**\n\n"
                    "Kripya channel Chat ID aur Invite Link send karein separated by space.\n"
                    "Format: `[channel_id] [invite_link]`\n\n"
                    "Example: `-100234567890 https://t.me/+AbCdEf...`"
                ),
                reply_markup=cancel_markup
            )
            
        elif data == "adm_remove_channel":
            admin_states[user_id] = "awaiting_remove_channel"
            await query.edit_message_text(
                text="➖ **Channel remove karein**\n\nJis channel ko delete karna hai uska index enter karein (e.g. `1`):",
                reply_markup=cancel_markup
            )
            
        elif data == "adm_broadcast":
            admin_states[user_id] = "awaiting_broadcast"
            await query.edit_message_text(
                text=(
                    "📢 **Awaiting Broadcast Content**\n\n"
                    "Ab aap jo bhi message sabhi users ko bhejna chahte hain, use yahan send ya forward karein.\n"
                    "Aap photos, videos, styled text, button kuch bhi send kar sakte hain!"
                ),
                reply_markup=cancel_markup
            )
            
    # --- Verify Channel Membership & Grant 3 Bills ---
    elif data == "btn_verify_join":
        is_member, _ = await check_channel_memberships(context.bot, chat_id)
        if is_member:
            if not settings.get("joined_channel", False):
                settings["joined_channel"] = True
                settings["credits"] = settings.get("credits", 0) + 3  # Join channel awards exactly 3 bills
                save_user_settings(chat_id, settings)
                
                # Award referrer
                referred_by = settings.get("referred_by", "")
                if referred_by and not settings.get("referral_rewarded", False):
                    settings["referral_rewarded"] = True
                    save_user_settings(chat_id, settings)
                    
                    config = get_global_config()
                    referral_reward = config.get("referral_reward", 5)
                    ref_settings = get_user_settings(referred_by)
                    ref_settings["credits"] = ref_settings.get("credits", 0) + referral_reward
                    ref_settings["referrals_count"] = ref_settings.get("referrals_count", 0) + 1
                    save_user_settings(referred_by, ref_settings)
                    try:
                        await context.bot.send_message(
                            chat_id=referred_by,
                            text=f"🎉 **Referral Success!**\n\nAapke referral link se kisi ne bot join kiya hai. Aapko **+{referral_reward} free bills** mil gaye hain!"
                        )
                    except Exception:
                        pass
                
                success_text = "🎉 **Membership Verified!**\n\nAapko **3 free bills** mil gaye hain."
            else:
                success_text = "🎉 **Membership Confirmed!**\n\nAap abhi bhi required channels me subscribed hain."
                
            await query.edit_message_text(text=success_text, parse_mode="Markdown")
            
            # Send main controls using reply keyboard
            await context.bot.send_message(
                chat_id=chat_id,
                text="Niche diye gaye keyboard se bill generate karein:",
                reply_markup=make_main_keyboard(chat_id)
            )
        else:
            config = get_global_config()
            channels = config.get("channels", ["@ai_receipt_channel"])
            invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
            
            keyboard = []
            for i, channel in enumerate(channels):
                link = invite_links[i] if i < len(invite_links) else f"https://t.me/{channel.replace('@', '')}"
                keyboard.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
            keyboard.append([InlineKeyboardButton("🔄 Verify Memberships & Unlock 3 Bills", callback_data="btn_verify_join")])
            
            await query.edit_message_text(
                text=(
                    f"❌ **Verification Failed!**\n\n"
                    f"Kripya pehle sabhi required channels ko join karein."
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if admin is currently in broadcast state (supports media/photo uploads too)
    if user_id == ADMIN_ID and admin_states.get(user_id) == "awaiting_broadcast":
        admin_states.pop(user_id, None)
        # Execute message forwarding broadcast in background
        asyncio.create_task(execute_broadcast(update.message, context))
        return

    text = update.message.text.strip() if update.message.text else ""
    
    # 1. Admin config inputs
    if user_id == ADMIN_ID and user_id in admin_states:
        state = admin_states[user_id]
        config = get_global_config()
        
        if state == "awaiting_cooldown":
            try:
                val = int(text)
                config["cooling_period"] = val
                save_global_config(config)
                await update.message.reply_text(f"✅ Cooling period updated to **{val} seconds**.", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ Galat input. Ek integer value enter karein.")
            admin_states.pop(user_id, None)
            
        elif state == "awaiting_add_channel":
            parts = text.split()
            if len(parts) >= 2:
                channel_id = parts[0]
                invite_link = parts[1]
                
                if not (channel_id.startswith("@") or channel_id.startswith("-100")):
                    await update.message.reply_text("❌ Channel ID must start with @ or -100.")
                    return
                    
                channels = config.get("channels", ["@ai_receipt_channel"])
                invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
                
                channels.append(channel_id)
                invite_links.append(invite_link)
                config["channels"] = channels
                config["invite_links"] = invite_links
                save_global_config(config)
                
                await update.message.reply_text(
                    f"✅ Channel added!\n• ID: `{channel_id}`\n• Link: {invite_link}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Invalid format. Use: `[channel_id] [invite_link]`")
            admin_states.pop(user_id, None)
            
        elif state == "awaiting_remove_channel":
            try:
                idx = int(text) - 1
                channels = config.get("channels", ["@ai_receipt_channel"])
                invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
                
                if 0 <= idx < len(channels):
                    removed_ch = channels.pop(idx)
                    if idx < len(invite_links):
                        invite_links.pop(idx)
                        
                    config["channels"] = channels
                    config["invite_links"] = invite_links
                    save_global_config(config)
                    
                    await update.message.reply_text(f"✅ Removed channel: `{removed_ch}`.", parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ Index out of range.")
            except ValueError:
                await update.message.reply_text("❌ Index value ek valid number hona chahiye.")
            admin_states.pop(user_id, None)
            
        return

    # 2. Reply Keyboard button actions
    if text == "⚡ Generate Bill":
        settings = get_user_settings(chat_id)
        allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=True)
        if not allowed:
            return
            
        await update.message.reply_text("⏳ Aapka bill generate kiya ja raha hai... kripya thoda intezar karein.")
        try:
            await render_and_send_receipt(chat_id, context, settings)
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating receipt: {e}")
            
        await update.message.reply_text(
            text=f"🧾 Menu controls (Balance: `{settings.get('credits', 0)} bills`):",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return
        
    elif text == "👥 Refer & Earn":
        settings = get_user_settings(chat_id)
        config = get_global_config()
        ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
        refer_reward = config.get("referral_reward", 5)
        
        refer_text = (
            f"👥 **Refer & Earn Program**\n\n"
            f"Apne dosto ko bot refer karein aur dher saare free bills kamayein!\n\n"
            f"🔗 **Aapka Referral Link**:\n"
            f"`{ref_link}`\n\n"
            f"🎁 Har successful refer par (jab aapka dost join karega) aapko **+{refer_reward} free bills** milenge!\n\n"
            f"📊 **Aapke Stats**:\n"
            f"• Referred friends: `{settings.get('referrals_count', 0)}`/`{settings.get('referrals_count', 0)}` (verified)\n"
            f"• Bills Balance: `{settings.get('credits', 0)} bills`"
        )
        
        await update.message.reply_text(
            text=refer_text,
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return

    elif text == "💰 My Balance":
        settings = get_user_settings(chat_id)
        balance_text = (
            f"💰 **Aapka Balance Detail**:\n\n"
            f"• Available Bills: `{settings.get('credits', 0)} free bills`\n"
            f"• Total Referred Friends: `{settings.get('referrals_count', 0)}`"
        )
        await update.message.reply_text(
            text=balance_text,
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return

    elif text == "❓ Support & Help":
        help_text = (
            f"❓ **Help & Support Panel**\n\n"
            f"Agar aapko bot use karne me koi dikkat aa rahi hai ya koi sawal hai, toh aap humse contact kar sakte hain.\n\n"
            f"✍️ **Contact Support**: @admin_support_handle\n\n"
            f"💡 **Kaise use karein?**\n"
            f"1. Sabhi required channels join karein.\n"
            f"2. Niche diye gaye `⚡ Generate Bill` button par click karein.\n"
            f"3. Instantly 3:4 aspect ratio ka authentic bill generate ho jayega."
        )
        await update.message.reply_text(
            text=help_text,
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return

    elif text == "👑 Admin Panel" and user_id == ADMIN_ID:
        await admin_cmd(update, context)
        return
        
    elif text == "▶️ Start Auto-Stream" and user_id == ADMIN_ID:
        if chat_id in active_tasks:
            return
        settings = get_user_settings(chat_id)
        task = asyncio.create_task(admin_stream_task(chat_id, context, settings))
        active_tasks[chat_id] = task
        await update.message.reply_text(
            "▶️ **Auto-Stream Active**\n\nGenerating unlimited bills every 2.5 seconds...",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return
        
    elif text == "⏹ Stop Auto-Stream" and user_id == ADMIN_ID:
        task = active_tasks.get(chat_id)
        if task:
            task.cancel()
            active_tasks.pop(chat_id, None)
        await update.message.reply_text(
            "⏹ **Auto-Stream Stopped**\n\nYou can generate bills individually or resume stream.",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        return

    # Standard photo warning
    if update.message.photo:
        await update.message.reply_text(
            "💡 **Notice**: Sending reference photos is no longer required. The bot generates bills directly using our custom restaurant layout. Just click **Generate Bill** below!"
        )

# ─── Main Bot Initialization ───

def main():
    download_fonts()
    
    # Start Render keep-alive health server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    app = Application.builder().token(TOKEN).build()
    
    # Register commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", start_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    app.add_handler(CommandHandler("giveall", giveall_cmd))
    app.add_handler(CommandHandler("setrefer", setrefer_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Register text & media message handler supporting all types (crucial for broadcast cloning)
    app.add_handler(MessageHandler(filters.ALL, handle_text_message))
    
    print("🧾 Indian Cafes & Hotels Bill Generator Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
