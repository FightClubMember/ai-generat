import os
import io
import json
import time
import asyncio
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from generator import generate_receipt_image, download_fonts
from analyzer import analyze_receipt_style, load_user_style, save_user_style

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

# ─── Global Config File (Admin parameters persist here) ───
GLOBAL_CONFIG_PATH = "styles/global_config.json"

def get_global_config():
    os.makedirs("styles", exist_ok=True)
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default settings
    default_config = {
        "channels": ["@ai_receipt_channel"],
        "invite_links": ["https://t.me/ai_receipt_channel"],
        "cooling_period": 30
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
    "credits": 3,              # Users get 3 free bills initially
    "joined_channel": False,   # Tracks if they joined and claimed +50 reward
    "last_claim_date": "",     # Tracks daily bonus claims (YYYY-MM-DD)
    "last_gen_time": 0,        # Cooldown check
    "referred_by": "",         # Referrer ID
    "referral_rewarded": False # Prevent double rewarding
}

def get_user_settings(chat_id):
    if chat_id not in user_settings:
        settings_path = f"styles/{chat_id}_settings.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    user_settings[chat_id] = json.load(f)
            except Exception:
                user_settings[chat_id] = DEFAULT_SETTINGS.copy()
        else:
            user_settings[chat_id] = DEFAULT_SETTINGS.copy()
            
    # Ensure default fields are present
    for k, v in DEFAULT_SETTINGS.items():
        if k not in user_settings[chat_id]:
            user_settings[chat_id][k] = v
            
    return user_settings[chat_id]

def save_user_settings(chat_id, settings):
    os.makedirs("styles", exist_ok=True)
    settings_path = f"styles/{chat_id}_settings.json"
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Failed to save settings for {chat_id}: {e}")

# ─── Keep-Alive HTTP Server (for Render deployment) ───

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
            # Bypass check during local testing if channel is not found
            if "Chat not found" in str(e) or "chat not found" in str(e) or "bot is not a member" in str(e):
                print(f"WARNING: Channel {channel} not found or bot is not admin. Bypassing check.")
                continue
            return False, channel
    return True, None

async def enforce_membership_and_credits(chat_id, context, settings, consume_credit=False):
    """
    Checks channel memberships, cooldowns, and credit balance.
    If membership is missing, prompts to join and awards +50 credits once verified.
    Handles referral awards (+5 credits to referrer).
    Checks cooldown periods.
    """
    config = get_global_config()
    channels = config.get("channels", ["@ai_receipt_channel"])
    invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
    
    # 1. Enforce Channel Memberships
    is_member, blocked_channel = await check_channel_memberships(context.bot, chat_id)
    
    if not is_member:
        # User left a channel! Deduct reward credits
        if settings.get("joined_channel", False):
            settings["joined_channel"] = False
            settings["credits"] = max(0, settings.get("credits", 3) - 50)
            save_user_settings(chat_id, settings)
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ **Warning**: You left one of our official channels! 50 reward credits have been deducted."
            )
            
        # Display join prompt
        keyboard = []
        for i, channel in enumerate(channels):
            link = invite_links[i] if i < len(invite_links) else f"https://t.me/{channel.replace('@', '')}"
            keyboard.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
            
        keyboard.append([InlineKeyboardButton("🔄 Verify Memberships & Claim +50 Credits", callback_data="btn_verify_join")])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ **Access Restricted!**\n\n"
                f"To use the bot, you must be a member of all required channels first!\n\n"
                f"Join them and click verify to unlock **50 free credits**!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return False
        
    # User is in all channels. Reward if not marked.
    if not settings.get("joined_channel", False):
        settings["joined_channel"] = True
        settings["credits"] = settings.get("credits", 3) + 50
        save_user_settings(chat_id, settings)
        
        # Handle referral rewards
        referred_by = settings.get("referred_by", "")
        if referred_by and not settings.get("referral_rewarded", False):
            settings["referral_rewarded"] = True
            save_user_settings(chat_id, settings)
            
            # Award 5 credits to referrer
            ref_settings = get_user_settings(referred_by)
            ref_settings["credits"] = ref_settings.get("credits", 3) + 5
            save_user_settings(referred_by, ref_settings)
            
            try:
                await context.bot.send_message(
                    chat_id=referred_by,
                    text="🎉 **Referral Success!**\n\nSomeone joined using your link! You earned **+5 free bills**."
                )
            except Exception:
                pass
                
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 **Thank you for joining our channels!**\nAdded **+50 free credits** to your balance."
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
                text=f"⚠️ **Cooling Period Active!**\n\nPlease wait **{remaining} seconds** before generating another bill."
            )
            return False

    # 3. Check Credit Balance
    credits = settings.get("credits", 3)
    if consume_credit:
        if credits < 1:
            ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"❌ **Out of Credits!**\n\n"
                    f"You have used all your free bills.\n\n"
                    f"🔗 **Refer & Earn +5 bills!**\n"
                    f"Share your referral link with friends to get credits:\n"
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
    # Renders the Chinese Restaurant bill exactly as sended in the reference image
    # Tabletop layout, striped background, and bold fonts are active by default
    img = await asyncio.to_thread(generate_receipt_image)
    
    # Save image to bytes stream
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    
    caption = f"🧾 Here is your restaurant bill!\n💰 Remaining Balance: `{settings.get('credits', 3)} credits`"
        
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=buf,
        caption=caption,
        parse_mode="Markdown",
        filename="bill.png"
    )

# ─── Commands & Keyboards ───

def make_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡ Generate Bill", callback_data="btn_gen_one")],
        [InlineKeyboardButton("🎁 Daily Bonus (+5)", callback_data="btn_claim_daily")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if they joined via a referral link
    settings = get_user_settings(chat_id)
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].split("_")[1])
            # Only set if they don't already have a referrer and aren't referring themselves
            if not settings.get("referred_by") and referrer_id != user_id:
                settings["referred_by"] = str(referrer_id)
                save_user_settings(chat_id, settings)
        except Exception as e:
            print(f"Error parsing referral ID: {e}")
            
    credits = settings.get("credits", 3)
    config = get_global_config()
    cooldown = config.get("cooling_period", 30)
    
    ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
    
    welcome_text = (
        f"👑 **Royal Chinese Garden Bill Generator** 🧾\n\n"
        f"Generate authentic restaurant bills instantly.\n\n"
        f"💰 **Available Bills**: `{credits} free bills`\n"
        f"⏱ **Cooling Period**: `{cooldown}s`\n\n"
        f"🔗 **Refer & Earn**:\n"
        f"Share your referral link to earn **+5 bills** per success!\n"
        f"`{ref_link}`"
    )
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=make_main_keyboard(),
        parse_mode="Markdown"
    )

# ─── Admin Control Panel ───

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
        
    config = get_global_config()
    channels = config.get("channels", ["@ai_receipt_channel"])
    invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
    cooldown = config.get("cooling_period", 30)
    
    text = (
        "👑 **Admin Control Panel**\n\n"
        f"• **Cooling Period**: `{cooldown}s`\n"
        f"• **Required Channels**:\n"
    )
    for i, ch in enumerate(channels):
        link = invite_links[i] if i < len(invite_links) else "N/A"
        text += f"  {i+1}. `{ch}` -> [Invite Link]({link})\n"
        
    keyboard = [
        [InlineKeyboardButton("⏱ Edit Cooling Period", callback_data="adm_edit_cooldown")],
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

# ─── Message & Callback Handlers ───

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    settings = get_user_settings(chat_id)
    data = query.data
    
    # --- Admin Button Actions ---
    if data.startswith("adm_"):
        if user_id != ADMIN_ID:
            return
            
        if data == "adm_edit_cooldown":
            admin_states[user_id] = "awaiting_cooldown"
            await query.edit_message_text("⏱ **Awaiting Cooldown Cooldown Input**\n\nPlease send the cooling period in seconds (e.g. `60`):")
            
        elif data == "adm_add_channel":
            admin_states[user_id] = "awaiting_add_channel"
            await query.edit_message_text(
                "➕ **Awaiting Channel ID & Link**\n\n"
                "Please send the channel Chat ID and Invite Link separated by space.\n"
                "Format: `[channel_id] [invite_link]`\n\n"
                "Example: `-100234567890 https://t.me/+AbCdEf...`"
            )
            
        elif data == "adm_remove_channel":
            admin_states[user_id] = "awaiting_remove_channel"
            await query.edit_message_text(
                "➖ **Awaiting Channel Index**\n\n"
                "Please send the index number of the channel you want to remove (e.g. `1` or `2`):"
            )
            
    # --- User Button Actions ---
    elif data == "btn_menu_main":
        credits = settings.get("credits", 3)
        config = get_global_config()
        cooldown = config.get("cooling_period", 30)
        ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{chat_id}"
        
        await query.edit_message_text(
            text=(
                f"👑 **Royal Chinese Garden Bill Generator** 🧾\n\n"
                f"💰 **Available Bills**: `{credits} free bills`\n"
                f"⏱ **Cooling Period**: `{cooldown}s`\n\n"
                f"🔗 **Referral Link**:\n"
                f"`{ref_link}`"
            ),
            reply_markup=make_main_keyboard(),
            parse_mode="Markdown"
        )
        
    elif data == "btn_gen_one":
        # Check channel subscription and cooldown
        allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=True)
        if not allowed:
            return
            
        await query.edit_message_text("⏳ Rendering your custom receipt... please wait.")
        try:
            await render_and_send_receipt(chat_id, context, settings)
        except Exception as e:
            await query.message.reply_text(f"❌ Error generating receipt: {e}")
            
        # Restore controls
        await query.message.reply_text(
            text=f"🧾 Menu controls (Balance: `{settings.get('credits', 3)} credits`):",
            reply_markup=make_main_keyboard(),
            parse_mode="Markdown"
        )
        
    elif data == "btn_verify_join":
        is_member, _ = await check_channel_memberships(context.bot, chat_id)
        if is_member:
            if not settings.get("joined_channel", False):
                settings["joined_channel"] = True
                settings["credits"] = settings.get("credits", 3) + 50
                save_user_settings(chat_id, settings)
                
                # Check for referral rewards
                referred_by = settings.get("referred_by", "")
                if referred_by and not settings.get("referral_rewarded", False):
                    settings["referral_rewarded"] = True
                    save_user_settings(chat_id, settings)
                    
                    ref_settings = get_user_settings(referred_by)
                    ref_settings["credits"] = ref_settings.get("credits", 3) + 5
                    save_user_settings(referred_by, ref_settings)
                    try:
                        await context.bot.send_message(
                            chat_id=referred_by,
                            text="🎉 **Referral Success!**\n\nSomeone joined using your link! You earned **+5 free bills**."
                        )
                    except Exception:
                        pass
                
                success_text = "🎉 **Membership Verified!**\n\nAdded **+50 free credits** to your balance."
            else:
                success_text = "🎉 **Membership Confirmed!**\n\nYou are still subscribed to required channels."
                
            await query.edit_message_text(
                text=success_text,
                reply_markup=make_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            config = get_global_config()
            channels = config.get("channels", ["@ai_receipt_channel"])
            invite_links = config.get("invite_links", ["https://t.me/ai_receipt_channel"])
            
            keyboard = []
            for i, channel in enumerate(channels):
                link = invite_links[i] if i < len(invite_links) else f"https://t.me/{channel.replace('@', '')}"
                keyboard.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
            keyboard.append([InlineKeyboardButton("🔄 Verify Memberships & Claim +50 Credits", callback_data="btn_verify_join")])
            
            await query.edit_message_text(
                text=(
                    f"❌ **Verification Failed!**\n\n"
                    f"Please make sure you have joined all of our official channels first before trying to verify."
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
    elif data == "btn_claim_daily":
        today_str = datetime.now().strftime("%Y-%m-%d")
        last_claim = settings.get("last_claim_date", "")
        
        if last_claim == today_str:
            await query.edit_message_text(
                text="❌ **Already Claimed!**\n\nYou have already claimed your daily bonus today. Come back tomorrow!",
                reply_markup=make_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            settings["last_claim_date"] = today_str
            settings["credits"] = settings.get("credits", 3) + 5
            save_user_settings(chat_id, settings)
            
            await query.edit_message_text(
                text=(
                    f"🎉 **Daily Bonus Claimed!**\n\n"
                    f"Added **+5 credits** to your balance.\n"
                    f"💰 Total Balance: `{settings['credits']} credits`"
                ),
                reply_markup=make_main_keyboard(),
                parse_mode="Markdown"
            )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Verify if admin is in configuration state
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
                await update.message.reply_text("❌ Invalid input. Please send an integer value.")
            admin_states.pop(user_id, None)
            
        elif state == "awaiting_add_channel":
            parts = text.split()
            if len(parts) >= 2:
                channel_id = parts[0]
                invite_link = parts[1]
                
                if not (channel_id.startswith("@") or channel_id.startswith("-100")):
                    await update.message.reply_text("❌ Channel ID must start with @ (public) or -100 (private).")
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
                await update.message.reply_text("❌ Invalid format. Please send: `[channel_id] [invite_link]`")
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
                await update.message.reply_text("❌ Please enter a valid index number.")
            admin_states.pop(user_id, None)
            
        return

    # Standard users who send photos (Reference/Inspiration photos are disabled as per request)
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
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", start_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_text_message))
    
    print("🧾 Royal Chinese Garden Bill Generator Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
