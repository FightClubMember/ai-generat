import os
import io
import json
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
        # Fallback to dummy token or warning (will be resolved before launching)
        TOKEN = "YOUR_BOT_TOKEN_HERE"

# Required Channel for Force-Join Membership check
# Users must subscribe to this channel to use the bot
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@ai_receipt_channel")

# Global state
active_tasks = {}  # chat_id -> asyncio.Task
user_settings = {}  # chat_id -> dict

DEFAULT_SETTINGS = {
    "template": "grocery",
    "realism": "tabletop",
    "currency": "INR",
    "font": "receipt",
    "credits": 10,          # Start with 10 free credits
    "joined_channel": False,  # Tracks if they joined and claimed +50 reward
    "last_claim_date": ""   # Tracks daily bonus claims (YYYY-MM-DD)
}

TEMPLATE_LABELS = {
    "grocery": "🛒 Grocery (Kirana / D-Mart)",
    "cafe": "🍲 Food (Restaurant / Cafe)",
    "retail": "👗 Cloth (Apparel / Manyavar)",
    "gas": "⛽ Petrol Pump (Fuel / IOCL)"
}

REALISM_LABELS = {
    "clean": "⚡ Clean Digital",
    "thermal": "🧾 Vintage Thermal",
    "tabletop": "📸 Tabletop Photoreal"
}

CURRENCY_LABELS = {
    "INR": "₹ INR",
    "USD": "$ USD",
    "EUR": "€ EUR",
    "GBP": "£ GBP"
}

FONT_LABELS = {
    "receipt": "Roboto Mono (Monospace)",
    "default": "Browser Default Font"
}

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
    # Render binds the port to the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RenderHealthCheckHandler)
    print(f"Health check server listening on port {port}...")
    server.serve_forever()

# ─── Helper Functions ───

def get_user_settings(chat_id):
    if chat_id not in user_settings:
        # Try to load existing settings or use default
        settings_path = f"styles/{chat_id}_settings.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    user_settings[chat_id] = json.load(f)
            except Exception:
                user_settings[chat_id] = DEFAULT_SETTINGS.copy()
        else:
            user_settings[chat_id] = DEFAULT_SETTINGS.copy()
    
    # Ensure default fields are present if loaded from older settings files
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

# ─── Access Control: Channel check & Credits System ───

async def check_channel_member(bot, user_id):
    """Checks if a user is a member/admin of the required Telegram channel."""
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        # Status can be: 'creator', 'administrator', 'member', 'restricted', 'left', 'kicked'
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Channel membership check failed for user {user_id}: {e}")
        # Bypasses check during testing if the bot is not configured in the channel yet
        if "Chat not found" in str(e) or "chat not found" in str(e) or "bot is not a member" in str(e):
            print("WARNING: Chat not found or bot is not admin in channel. Bypassing check for development.")
            return True
    return False

async def enforce_membership_and_credits(chat_id, context, settings, consume_credit=False):
    """
    Verifies channel membership and credit balance.
    Blocks action and prompts re-joining or claiming daily credits if requirements are unmet.
    If membership was lost, deducts the 50-credit join reward.
    """
    # 1. Enforce Channel Membership
    is_member = await check_channel_member(context.bot, chat_id)
    
    if not is_member:
        # User left the channel! Deduct their reward credits.
        if settings.get("joined_channel", False):
            settings["joined_channel"] = False
            settings["credits"] = max(0, settings.get("credits", 10) - 50)
            save_user_settings(chat_id, settings)
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ **Warning**: You left our official channel! **50 credits** have been deducted from your balance."
            )
            
        # Display block panel
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Verify Membership & Claim +50 Credits", callback_data="btn_verify_join")]
        ]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ **Access Restricted!**\n\n"
                f"To use the bot, you must be a member of our official channel:\n"
                f"👉 {REQUIRED_CHANNEL}\n\n"
                f"Join now and click verify to instantly unlock **50 free credits**!"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return False
        
    # User is in the channel. If not already marked, reward them with +50 credits.
    if not settings.get("joined_channel", False):
        settings["joined_channel"] = True
        settings["credits"] = settings.get("credits", 10) + 50
        save_user_settings(chat_id, settings)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 **Thank you for joining our channel!**\nAdded **+50 free credits** to your balance."
        )

    # 2. Enforce Credits
    credits = settings.get("credits", 10)
    if consume_credit:
        if credits < 1:
            keyboard = [
                [InlineKeyboardButton("🎁 Claim Daily Credits (+5)", callback_data="btn_claim_daily")],
                [InlineKeyboardButton("⬅️ Main Menu", callback_data="btn_menu_main")]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "❌ **Out of Credits!**\n\n"
                    "You have 0 credits remaining.\n"
                    "Please claim your daily bonus below, or stay subscribed to our channel to unlock more benefits."
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return False
        else:
            # Deduct 1 credit
            settings["credits"] = credits - 1
            save_user_settings(chat_id, settings)
            
    return True

# ─── Rendering Helper ───

async def render_and_send_receipt(chat_id, context, settings, count_label=""):
    """Runs PIL receipt rendering in a background thread and sends it as a photo."""
    # Load user's reference style if any
    custom_style = load_user_style(chat_id)
    
    # Run the heavy image rendering operations in asyncio.to_thread
    img = await asyncio.to_thread(
        generate_receipt_image,
        template=settings["template"],
        realism=settings["realism"],
        currency=settings["currency"],
        font=settings["font"],
        custom_style=custom_style
    )
    
    # Save image to bytes stream
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    
    caption = f"🧾 Here is your {TEMPLATE_LABELS[settings['template']]} receipt!"
    if count_label:
        caption += f" ({count_label})"
    if custom_style and custom_style.get("detected"):
        caption += "\n🎨 Styled matching your reference photo."
    
    # Show remaining balance
    caption += f"\n💰 Remaining Balance: `{settings.get('credits', 10)} credits`"
        
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=buf,
        caption=caption,
        parse_mode="Markdown",
        filename="receipt.png"
    )

async def generation_stream_task(chat_id, context, settings):
    """Loop that continuously generates and sends receipts, checking requirements and consuming credits."""
    count = 1
    try:
        while True:
            # Fetch latest settings to check credit count
            settings = get_user_settings(chat_id)
            
            # Verify channel subscription and consume 1 credit
            allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=True)
            if not allowed:
                # membership checks or credit limits blocked generation, stop stream
                break
                
            await render_and_send_receipt(chat_id, context, settings, count_label=f"#{count}")
            count += 1
            
            # Random delay between 1.5 and 3.5 seconds
            import random
            delay = random.uniform(1.5, 3.5)
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        # Task was cancelled, exit cleanly
        pass
    except Exception as e:
        print(f"Stream error for chat {chat_id}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🛑 Generation stream stopped due to an error: {e}"
        )
    finally:
        active_tasks.pop(chat_id, None)

# ─── Telegram Bot Commands & Menus ───

def make_main_keyboard(chat_id):
    is_streaming = chat_id in active_tasks
    
    keyboard = [
        [
            InlineKeyboardButton("⚡ Generate One", callback_data="btn_gen_one"),
            InlineKeyboardButton("🛠 Configure Bot", callback_data="btn_menu_config")
        ],
        [
            InlineKeyboardButton(
                "⏹ Stop Stream" if is_streaming else "▶️ Start Stream", 
                callback_data="btn_stop_stream" if is_streaming else "btn_start_stream"
            )
        ]
    ]
    
    # Bottom control row: Reset style (if loaded) and claim daily bonus
    row3 = []
    style = load_user_style(chat_id)
    if style:
        row3.append(InlineKeyboardButton("🧹 Reset Style", callback_data="btn_reset_style"))
    row3.append(InlineKeyboardButton("🎁 Daily Bonus", callback_data="btn_claim_daily"))
    keyboard.append(row3)
        
    return InlineKeyboardMarkup(keyboard)

def make_config_keyboard(settings):
    # Layout cycles
    t_val = settings["template"]
    r_val = settings["realism"]
    c_val = settings["currency"]
    f_val = settings["font"]
    
    keyboard = [
        [InlineKeyboardButton(f"Template: {TEMPLATE_LABELS[t_val]}", callback_data="cycle_template")],
        [InlineKeyboardButton(f"Realism: {REALISM_LABELS[r_val]}", callback_data="cycle_realism")],
        [InlineKeyboardButton(f"Currency: {CURRENCY_LABELS[c_val]}", callback_data="cycle_currency")],
        [InlineKeyboardButton(f"Font: {FONT_LABELS[f_val]}", callback_data="cycle_font")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="btn_menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = get_user_settings(chat_id)
    credits = settings.get("credits", 10)
    
    welcome_text = (
        "📸 **Welcome to Premium Receipt Bot!**\n\n"
        "To start generating, **please send/upload an inspiration receipt photo first**.\n"
        "I will extract its exact paper and ink colors to generate new matching receipts!\n\n"
        f"💰 **Your Balance**: `{credits} credits`\n"
        f"*(Generations cost 1 credit each. Join {REQUIRED_CHANNEL} for +50 free credits!)*\n\n"
        "💡 **Features**:\n"
        "• **Indian Formats**: Supports Indian Food (Saravana/CCD), Groceries (Kirana/D-Mart), Clothing (Manyavar/Fabindia), and Petrol Pumps (litres/₹).\n"
        "• **Interactive Settings**: Cycle templates, realism filters, and currencies.\n"
        "• **Photo Realism**: Tabletop mode overlays the receipt on a dark wood or slate surface with perspective tilt, drop shadows, and 3D paper folds.\n\n"
        "⚠️ *You must send an inspiration photo before you can generate.*"
    )
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=make_main_keyboard(chat_id),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = get_user_settings(chat_id)
    data = query.data
    
    # --- Navigation ---
    if data == "btn_menu_main":
        credits = settings.get("credits", 10)
        await query.edit_message_text(
            text=(
                f"🧾 **Premium Receipt Generator Bot**\n\n"
                f"💰 **Your Balance**: `{credits} credits`\n"
                f"Use the buttons below to control the bot:"
            ),
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        
    elif data == "btn_menu_config":
        await query.edit_message_text(
            text="🛠 **Bot Configuration**\n\nClick on any parameter to cycle through options:",
            reply_markup=make_config_keyboard(settings),
            parse_mode="Markdown"
        )
        
    # --- Action Buttons ---
    elif data == "btn_gen_one":
        # Check if they have sent an inspiration photo
        style = load_user_style(chat_id)
        if not style:
            await query.edit_message_text(
                text="📸 **Inspiration Photo Required!**\n\nPlease upload/send a receipt photo first so I can analyze its style and layout to make the same receipt!",
                reply_markup=make_main_keyboard(chat_id),
                parse_mode="Markdown"
            )
            return
            
        # Verify force join channel and consume 1 credit
        allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=True)
        if not allowed:
            return
            
        # Generate one receipt in background task
        await query.edit_message_text(
            text="⏳ Rendering your custom receipt... please wait.",
            reply_markup=None
        )
        try:
            await render_and_send_receipt(chat_id, context, settings)
        except Exception as e:
            await query.message.reply_text(f"❌ Error generating receipt: {e}")
            
        # Restore main menu
        await query.message.reply_text(
            text=f"🧾 Menu controls (Balance: `{settings.get('credits', 10)} credits`):",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        
    elif data == "btn_start_stream":
        # Check if they have sent an inspiration photo
        style = load_user_style(chat_id)
        if not style:
            await query.edit_message_text(
                text="📸 **Inspiration Photo Required!**\n\nPlease upload/send a receipt photo first so I can analyze its style and layout to make the same receipt!",
                reply_markup=make_main_keyboard(chat_id),
                parse_mode="Markdown"
            )
            return
            
        # Verify force join channel first (don't consume yet, stream task consumes per loop)
        allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=False)
        if not allowed:
            return
            
        if chat_id in active_tasks:
            await query.edit_message_text(
                text="🔄 Stream is already active!",
                reply_markup=make_main_keyboard(chat_id)
            )
            return
            
        # Start background asyncio task
        task = asyncio.create_task(generation_stream_task(chat_id, context, settings))
        active_tasks[chat_id] = task
        
        await query.edit_message_text(
            text="▶️ **Auto-Generation Started**\n\nThe bot will send receipts every 1.5 - 3.5 seconds. Use the stop button below to pause.",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        
    elif data == "btn_stop_stream":
        task = active_tasks.get(chat_id)
        if task:
            task.cancel()
            active_tasks.pop(chat_id, None)
            
        await query.edit_message_text(
            text="⏹ **Auto-Generation Paused**\n\nStream has been stopped. You can generate individual receipts or configure settings.",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        
    elif data == "btn_reset_style":
        # Delete style files
        style_path = f"styles/{chat_id}_style.json"
        if os.path.exists(style_path):
            try:
                os.remove(style_path)
            except Exception:
                pass
        
        ref_path = f"references/{chat_id}_ref.png"
        if os.path.exists(ref_path):
            try:
                os.remove(ref_path)
            except Exception:
                pass
                
        await query.edit_message_text(
            text="🧹 **Reference Style Cleared**\n\nDefault colors (white paper, charcoal ink) will be used.",
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
        
    # --- Verify Channel Membership (Claim +50 Reward) ---
    elif data == "btn_verify_join":
        is_member = await check_channel_member(context.bot, chat_id)
        if is_member:
            if not settings.get("joined_channel", False):
                settings["joined_channel"] = True
                settings["credits"] = settings.get("credits", 10) + 50
                save_user_settings(chat_id, settings)
                success_text = "🎉 **Membership Verified!**\n\nThank you for joining our channel! Added **+50 free credits** to your balance."
            else:
                success_text = "🎉 **Membership Confirmed!**\n\nYou are still subscribed to our channel. Your credits are active."
                
            await query.edit_message_text(
                text=success_text,
                reply_markup=make_main_keyboard(chat_id),
                parse_mode="Markdown"
            )
        else:
            # Re-display join prompt with error
            await query.edit_message_text(
                text=(
                    f"❌ **Verification Failed!**\n\n"
                    f"It seems you have not joined our channel yet.\n"
                    f"Join here first:\n👉 {REQUIRED_CHANNEL}\n\n"
                    f"Then click verify below again to claim your +50 credits!"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
                    [InlineKeyboardButton("🔄 Verify Membership & Claim +50 Credits", callback_data="btn_verify_join")]
                ]),
                parse_mode="Markdown"
            )
            
    # --- Daily Credits Claims (+5 Credits) ---
    elif data == "btn_claim_daily":
        today_str = datetime.now().strftime("%Y-%m-%d")
        last_claim = settings.get("last_claim_date", "")
        
        if last_claim == today_str:
            await query.edit_message_text(
                text="❌ **Already Claimed!**\n\nYou have already claimed your daily bonus today. Come back tomorrow!",
                reply_markup=make_main_keyboard(chat_id),
                parse_mode="Markdown"
            )
        else:
            settings["last_claim_date"] = today_str
            settings["credits"] = settings.get("credits", 10) + 5
            save_user_settings(chat_id, settings)
            
            await query.edit_message_text(
                text=(
                    f"🎉 **Daily Bonus Claimed!**\n\n"
                    f"Added **+5 credits** to your balance.\n"
                    f"💰 Total Balance: `{settings['credits']} credits`"
                ),
                reply_markup=make_main_keyboard(chat_id),
                parse_mode="Markdown"
            )
            
    # --- Configuration Cycles ---
    elif data == "cycle_template":
        templates = ["grocery", "cafe", "retail", "gas"]
        current = settings["template"]
        next_template = templates[(templates.index(current) + 1) % len(templates)]
        settings["template"] = next_template
        save_user_settings(chat_id, settings)
        
        await query.edit_message_reply_markup(reply_markup=make_config_keyboard(settings))
        
    elif data == "cycle_realism":
        modes = ["clean", "thermal", "tabletop"]
        current = settings["realism"]
        next_mode = modes[(modes.index(current) + 1) % len(modes)]
        settings["realism"] = next_mode
        save_user_settings(chat_id, settings)
        
        await query.edit_message_reply_markup(reply_markup=make_config_keyboard(settings))
        
    elif data == "cycle_currency":
        currencies = ["INR", "USD", "EUR", "GBP"]
        current = settings["currency"]
        next_curr = currencies[(currencies.index(current) + 1) % len(currencies)]
        settings["currency"] = next_curr
        save_user_settings(chat_id, settings)
        
        await query.edit_message_reply_markup(reply_markup=make_config_keyboard(settings))
        
    elif data == "cycle_font":
        fonts = ["receipt", "default"]
        current = settings.get("font", "receipt")
        next_font = fonts[(fonts.index(current) + 1) % len(fonts)]
        settings["font"] = next_font
        save_user_settings(chat_id, settings)
        
        await query.edit_message_reply_markup(reply_markup=make_config_keyboard(settings))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes user reference images, extracts colors, and activates style matching."""
    chat_id = update.effective_chat.id
    settings = get_user_settings(chat_id)
    
    # Enforce channel membership (don't consume credit for uploading photos)
    allowed = await enforce_membership_and_credits(chat_id, context, settings, consume_credit=False)
    if not allowed:
        return
        
    # Show typing action while processing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    photo = update.message.photo[-1]  # Highest resolution
    file = await photo.get_file()
    
    # Download reference image to memory
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    buf.seek(0)
    
    # Save the file to local disk for analyzer
    os.makedirs("references", exist_ok=True)
    ref_path = f"references/{chat_id}_ref.png"
    with open(ref_path, "wb") as f:
        f.write(buf.read())
        
    # Analyze image colors
    style_data = await asyncio.to_thread(analyze_receipt_style, ref_path)
    
    if style_data.get("detected"):
        # Save style
        save_user_style(chat_id, style_data)
        
        bg_rgb = style_data["bg_color"]
        txt_rgb = style_data["text_color"]
        
        success_msg = (
            "📸 **Reference Image Analyzed Successfully!**\n\n"
            f"• **Paper Color**: RGB {bg_rgb}\n"
            f"• **Ink Color**: RGB {txt_rgb}\n\n"
            "Future receipts will use this color scheme to match your style. Use the buttons below to generate a sample!"
        )
        
        await update.message.reply_text(
            text=success_msg,
            reply_markup=make_main_keyboard(chat_id),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text="⚠️ Could not process image style. Make sure the image is clear and contains a single receipt document.",
            reply_markup=make_main_keyboard(chat_id)
        )

# ─── Main Bot Initialization ───

def main():
    # 1. Download Google fonts if missing
    download_fonts()
    
    # 2. Start keep-alive health check server on a background daemon thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # 3. Create Telegram Bot Application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", start_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🧾 Premium Receipt Generator Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
