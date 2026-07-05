import os
import io
import json
import asyncio
import threading
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

# Global state
active_tasks = {}  # chat_id -> asyncio.Task
user_settings = {}  # chat_id -> dict

DEFAULT_SETTINGS = {
    "template": "grocery",
    "realism": "tabletop",
    "currency": "USD",
    "font": "receipt"
}

TEMPLATE_LABELS = {
    "grocery": "🛒 Grocery Store",
    "cafe": "☕ Coffee Cafe",
    "retail": "👗 Luxe Retail",
    "gas": "⛽ Fuel Gas Station"
}

REALISM_LABELS = {
    "clean": "⚡ Clean Digital",
    "thermal": "🧾 Vintage Thermal",
    "tabletop": "📸 Tabletop Photoreal"
}

CURRENCY_LABELS = {
    "USD": "$ USD",
    "EUR": "€ EUR",
    "GBP": "£ GBP",
    "JPY": "¥ JPY"
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
    return user_settings[chat_id]

def save_user_settings(chat_id, settings):
    os.makedirs("styles", exist_ok=True)
    settings_path = f"styles/{chat_id}_settings.json"
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Failed to save settings for {chat_id}: {e}")

async def render_and_send_receipt(chat_id, context, settings, count_label=""):
    """Runs PIL receipt rendering in a background thread and sends it as a photo."""
    # Load user's reference style if any
    custom_style = load_user_style(chat_id)
    
    # Run the heavy image rendering operations in asyncio.to_thread
    # to avoid blocking the main asyncio event loop.
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
        
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=buf,
        caption=caption,
        filename="receipt.png"
    )

async def generation_stream_task(chat_id, context, settings):
    """Loop that continuously generates and sends receipts with a random delay."""
    count = 1
    try:
        while True:
            await render_and_send_receipt(chat_id, context, settings, count_label=f"#{count}")
            count += 1
            # Random delay between 1.5 and 3.5 seconds
            delay = round(asyncio.to_thread(lambda: float(io.open.__self__.random().uniform(1.5, 3.5))) if hasattr(io, "open") else 2.5) # simple random wait
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
    
    # Show "Reset Style" option if they have a reference image color style loaded
    style = load_user_style(chat_id)
    if style:
        keyboard.append([InlineKeyboardButton("🧹 Reset Reference Style", callback_data="btn_reset_style")])
        
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
    
    welcome_text = (
        "🧾 **Premium Receipt Generator Bot**\n\n"
        "Create high-quality, realistic receipts instantly!\n\n"
        "💡 **Features**:\n"
        "• **Interactive Settings**: Cycle templates, realism style, and currency.\n"
        "• **Photo Realism**: Tabletop mode overlays the receipt on a dark wood or slate surface with perspective tilt and realistic shadows.\n"
        "• **Color Style Matching**: Send me a photo of a receipt, and I will analyze and extract the paper/ink colors to generate receipts in that color style!\n\n"
        "Use the buttons below to control the bot:"
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
        await query.edit_message_text(
            text="🧾 **Premium Receipt Generator Bot**\n\nUse the buttons below to control the bot:",
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
        # Generate one receipt in background task
        # Edit keyboard to show loading state
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
            text="🧾 Menu controls:",
            reply_markup=make_main_keyboard(chat_id)
        )
        
    elif data == "btn_start_stream":
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
        # Delete style file
        style_path = f"styles/{chat_id}_style.json"
        if os.path.exists(style_path):
            try:
                os.remove(style_path)
            except Exception:
                pass
        
        # Also clean reference image if any
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
        currencies = ["USD", "EUR", "GBP", "JPY"]
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
