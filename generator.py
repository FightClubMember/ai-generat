import os
import random
import string
import urllib.request
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# ─── Font Downloader ───
FONT_DIR = "fonts"
FONT_PATH = os.path.join(FONT_DIR, "RobotoMono-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "RobotoMono-Bold.ttf")

def download_fonts():
    """Downloads Roboto Mono from Google Fonts raw repository if not present."""
    if not os.path.exists(FONT_DIR):
        os.makedirs(FONT_DIR)
        
    urls = {
        FONT_PATH: "https://github.com/googlefonts/RobotoMono/raw/main/fonts/ttf/RobotoMono-Regular.ttf",
        FONT_BOLD_PATH: "https://github.com/googlefonts/RobotoMono/raw/main/fonts/ttf/RobotoMono-Bold.ttf"
    }
    
    for path, url in urls.items():
        if not os.path.exists(path):
            print(f"Downloading font: {os.path.basename(path)}...")
            try:
                # Set a user-agent to avoid HTTP blocks
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response, open(path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Font saved to {path}")
            except Exception as e:
                print(f"Failed to download font {path}: {e}")

# Initial download attempt
download_fonts()

def get_font(size, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

# ─── Data Pools for Templates ───

CAFE_STORES = [
    ("The Daily Grind", "102 Espresso Way, Seattle, WA"),
    ("Espresso Express", "505 Brew Ave, Portland, OR"),
    ("Bean & Leaf Co.", "80 Coffee Rd, Boston, MA"),
    ("Brewed Awakening", "44 Latte Blvd, Austin, TX"),
]

CAFE_ITEMS = [
    ("Caramel Macchiato", 4.95),
    ("Vanilla Latte", 4.50),
    ("Cold Brew Coffee", 3.95),
    ("Flat White", 4.25),
    ("Warm Butter Croissant", 3.75),
    ("Avocado Sourdough Toast", 8.50),
    ("Double Chocolate Muffin", 3.50),
    ("Chai Tea Latte", 4.75),
    ("Bagel w/ Cream Cheese", 3.95),
    ("Lemon Loaf Cake", 3.25),
]

GROCERY_STORES = [
    ("MegaMart Grocery", "9900 Supercenter Dr, Bentonville, AR"),
    ("Fresh Foods Market", "250 Organic Way, Chicago, IL"),
    ("Pantry Plus", "1212 Staples St, Atlanta, GA"),
    ("Green Grocer", "400 Farmer Rd, Portland, OR"),
]

GROCERY_ITEMS = [
    ("Organic Milk 1G", 4.29),
    ("Farm Fresh Eggs 12ct", 3.89),
    ("Whole Wheat Bread", 2.49),
    ("Bananas Organic 3lb", 1.89),
    ("Shredded Cheddar 8oz", 3.19),
    ("Greek Yogurt 32oz", 4.99),
    ("Cereal Honey Oats", 3.79),
    ("Orange Juice 59oz", 4.49),
    ("Chicken Breast 2lb", 8.99),
    ("Basmati Rice 5lb", 6.49),
    ("Paper Towels 6pk", 7.99),
    ("Dish Soap 24oz", 2.99),
]

RETAIL_STORES = [
    ("AURA Boutique", "450 Fashion Ave, New York, NY"),
    ("LUXE Apparel", "888 Rodeo Dr, Beverly Hills, CA"),
    ("PRISM Electronics", "100 Tech Plaza, San Jose, CA"),
    ("VERDANT Home Goods", "33 Design Ln, Chicago, IL"),
]

RETAIL_ITEMS = [
    ("Minimalist Linen Shirt", 68.00),
    ("Designer Leather Wallet", 120.00),
    ("Premium Bluetooth Earbuds", 149.00),
    ("Silk Sleep Mask", 28.00),
    ("Scented Soy Candle", 24.00),
    ("Matte Black Notebook", 18.00),
    ("Wireless Charger Stand", 45.00),
    ("Wool Blend Socks Pack", 22.00),
    ("Smart Water Bottle", 39.00),
]

GAS_STORES = [
    ("APEX Fuel & Go", "1100 Highway 66, Flagstaff, AZ"),
    ("Summit Gas Station", "87 Interstate Rd, Denver, CO"),
    ("Star Express Convenience", "405 Pump St, Dallas, TX"),
    ("Pioneer Fuel", "320 Tanker Rd, Columbus, OH"),
]

GAS_ITEMS = [
    ("Monster Energy 16oz", 2.99),
    ("Glazed Donut", 1.29),
    ("Beef Jerky Original", 6.49),
    ("Windshield Washer Fluid", 4.99),
    ("Gummy Bears bag", 2.19),
    ("Bottled Water 1L", 1.99),
]

CURRENCIES = {
    "USD": ("$", "USD"),
    "EUR": ("€", "EUR"),
    "GBP": ("£", "GBP"),
    "JPY": ("¥", "JPY")
}

# ─── Helper Functions ───

def random_date():
    d = datetime.now() - timedelta(days=random.randint(0, 30),
                                  hours=random.randint(0, 23),
                                  minutes=random.randint(0, 59))
    return d.strftime("%Y-%m-%d %H:%M")

def get_receipt_data(template_name, currency_symbol):
    """Generates structured random data for the receipt."""
    date_str = random_date()
    card = "**** **** **** " + ''.join(random.choices(string.digits, k=4))
    receipt_no = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    auth_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    items = []
    
    if template_name == "cafe":
        store_name, store_addr = random.choice(CAFE_STORES)
        item_pool = CAFE_ITEMS
        count = random.randint(2, 6)
        for _ in range(count):
            name, u_price = random.choice(item_pool)
            qty = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            price = round(u_price * qty, 2)
            items.append((name, qty, price))
            
    elif template_name == "grocery":
        store_name, store_addr = random.choice(GROCERY_STORES)
        item_pool = GROCERY_ITEMS
        count = random.randint(4, 10)
        for _ in range(count):
            name, u_price = random.choice(item_pool)
            qty = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
            price = round(u_price * qty, 2)
            items.append((name, qty, price))
            
    elif template_name == "retail":
        store_name, store_addr = random.choice(RETAIL_STORES)
        item_pool = RETAIL_ITEMS
        count = random.randint(1, 4)
        for _ in range(count):
            name, u_price = random.choice(item_pool)
            qty = 1
            price = round(u_price * qty, 2)
            items.append((name, qty, price))
            
    else:  # gas
        store_name, store_addr = random.choice(GAS_STORES)
        # Gas receipts always have fuel as the primary item
        octane = random.choice([87, 89, 93])
        fuel_types = {87: "Regular 87", 89: "Plus 89", 93: "Premium 93"}
        gallons = round(random.uniform(8.0, 18.0), 3)
        price_per_gal = round(random.uniform(3.19, 4.69), 2)
        fuel_price = round(gallons * price_per_gal, 2)
        
        items.append((f"Unleaded {fuel_types[octane]}", f"{gallons:.3f} G", fuel_price))
        
        # Optionally add inside store items
        count = random.randint(0, 3)
        for _ in range(count):
            name, u_price = random.choice(GAS_ITEMS)
            qty = random.choices([1, 2], weights=[90, 10])[0]
            price = round(u_price * qty, 2)
            items.append((name, qty, price))
            
    subtotal = round(sum(p for _, _, p in items), 2)
    tax_rate = round(random.uniform(0.05, 0.09), 3)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    return {
        "store_name": store_name,
        "store_addr": store_addr,
        "date_str": date_str,
        "card": card,
        "receipt_no": receipt_no,
        "auth_code": auth_code,
        "items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
    }

# ─── Tabletop Background Generators ───

def generate_wood_background(width, height):
    """Generates a procedural dark wood table texture."""
    # Base warm dark brown color
    bg = Image.new("RGB", (width, height), (35, 23, 15))
    draw = ImageDraw.Draw(bg)
    
    # Draw vertical wood planks
    plank_width = 80
    for x in range(0, width, plank_width):
        # Draw slightly different brown tones
        r_offset = random.randint(-4, 4)
        g_offset = random.randint(-3, 3)
        b_offset = random.randint(-2, 2)
        
        plank_color = (max(0, 35 + r_offset), max(0, 23 + g_offset), max(0, 15 + b_offset))
        draw.rectangle([x, 0, x + plank_width, height], fill=plank_color)
        
        # Plank divider line
        draw.line([x, 0, x, height], fill=(15, 10, 5), width=1)
        
    # Apply heavy horizontal blur to blend plank colors into wood grain
    bg = bg.filter(ImageFilter.BoxBlur(15))
    
    # Draw fine wood grains
    grain_draw = ImageDraw.Draw(bg)
    for _ in range(120):
        gx = random.randint(0, width)
        gw = random.randint(2, 6)
        gh = random.randint(150, height)
        gy = random.randint(-50, height)
        # Grain color is slightly darker/warmer brown
        grain_color = (25, 16, 10)
        grain_draw.rectangle([gx, gy, gx + gw, gy + gh], fill=grain_color)
        
    # Soften grain
    bg = bg.filter(ImageFilter.GaussianBlur(radius=8))
    
    # Add fine wood fiber noise
    noise = Image.effect_noise((width, height), 12)
    noise_rgb = noise.convert("RGB")
    bg = Image.blend(bg, noise_rgb, 0.08)
    
    # Darken vignette (corners shadow)
    vignette = Image.new("L", (width, height), 255)
    v_draw = ImageDraw.Draw(vignette)
    cx, cy = width // 2, height // 2
    for r in range(max(width, height), 0, -25):
        alpha = int(255 - (r / max(width, height)) * 140)
        v_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))
    bg = Image.composite(bg, Image.new("RGB", (width, height), (5, 3, 2)), vignette)
    
    return bg

def generate_slate_background(width, height):
    """Generates a procedural slate / concrete tabletop texture."""
    # Base grey slate color
    bg = Image.new("RGB", (width, height), (55, 58, 62))
    
    # Multiple noise layers at different frequencies/blurs
    noise1 = Image.effect_noise((width, height), 22).convert("RGB")
    bg = Image.blend(bg, noise1, 0.12)
    
    # Draw concrete cracks / splotches
    draw = ImageDraw.Draw(bg)
    for _ in range(15):
        sx = random.randint(0, width)
        sy = random.randint(0, height)
        sr = random.randint(10, 80)
        color = random.choice([(45, 48, 52), (65, 68, 72)])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=color)
        
    bg = bg.filter(ImageFilter.GaussianBlur(12))
    
    # Final fine sand texture
    noise2 = Image.effect_noise((width, height), 8).convert("RGB")
    bg = Image.blend(bg, noise2, 0.05)
    
    # Dark vignette
    vignette = Image.new("L", (width, height), 255)
    v_draw = ImageDraw.Draw(vignette)
    cx, cy = width // 2, height // 2
    for r in range(max(width, height), 0, -20):
        alpha = int(255 - (r / max(width, height)) * 160)
        v_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    vignette = vignette.filter(ImageFilter.GaussianBlur(30))
    bg = Image.composite(bg, Image.new("RGB", (width, height), (15, 16, 18)), vignette)
    
    return bg

# ─── Crease/Fold Lines ───

def draw_3d_creases(receipt_img, bg_color, text_color):
    """Draws realistic highlight/shadow pairs to simulate 3D paper folds."""
    draw = ImageDraw.Draw(receipt_img, "RGBA")
    w, h = receipt_img.size
    
    # Determine highlight and shadow colors based on text/background colors
    # For a light background, highlight is white, shadow is grey/dark
    bg_lum = sum(bg_color) / 3
    if bg_lum > 120:
        highlight_color = (255, 255, 255, 20)  # semi-transparent white
        shadow_color = (0, 0, 0, 15)          # semi-transparent dark grey
    else:
        highlight_color = (255, 255, 255, 15)
        shadow_color = (0, 0, 0, 25)
        
    num_creases = random.randint(1, 3)
    for _ in range(num_creases):
        # Line spans either horizontally or diagonally
        y_start = random.randint(h // 6, h * 5 // 6)
        y_end = y_start + random.randint(-40, 40)
        
        # Highlight line
        draw.line([-10, y_start, w + 10, y_end], fill=highlight_color, width=2)
        # Shadow line directly below it (1px offset)
        draw.line([-10, y_start + 1, w + 10, y_end + 1], fill=shadow_color, width=2)
        
    return receipt_img

# ─── Core Receipt Canvas Generator ───

def draw_receipt_canvas(data, template_name, currency_symbol, font_style, bg_color, text_color):
    """Renders the textual receipt onto a white/tinted canvas."""
    width = 380
    lines = []
    
    store_name = data["store_name"]
    store_addr = data["store_addr"]
    date_str = data["date_str"]
    receipt_no = data["receipt_no"]
    items = data["items"]
    subtotal = data["subtotal"]
    tax_rate = data["tax_rate"]
    tax = data["tax"]
    total = data["total"]
    card = data["card"]
    auth_code = data["auth_code"]
    
    # Build text headers based on template
    if template_name == "cafe":
        lines.append(("   " + store_name.upper(), True))
        lines.append(("   " + store_addr, False))
        lines.append((f"   Tel: ({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}", False))
        lines.append(("─" * 38, False))
        lines.append(("   ☕ CAFE REWARD MEMBER", True))
        lines.append((f"   Date: {date_str}", False))
        lines.append((f"   Ticket: #{receipt_no}", False))
        lines.append((f"   Cashier: {random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}", False))
        lines.append(("─" * 38, False))
        lines.append(("", False))
        
        for name, qty, price in items:
            lines.append((f"   {name:<22} {qty:1d}   {currency_symbol}{price:>6.2f}", False))
            
        lines.append(("", False))
        lines.append(("─" * 38, False))
        lines.append((f"   SUBTOTAL{'':14s}{currency_symbol}{subtotal:>6.2f}", False))
        lines.append((f"   TAX ({tax_rate*100:.1f}%){'':10s}{currency_symbol}{tax:>6.2f}", False))
        lines.append((f"   TOTAL{'':17s}{currency_symbol}{total:>6.2f}", True))
        lines.append(("─" * 38, False))
        lines.append((f"   Paid via Card: {card}", False))
        lines.append((f"   Auth: {auth_code}", False))
        lines.append(("", False))
        lines.append(("     WiFi Network: CAFE_GUEST_5G", False))
        lines.append(("     WiFi Pass:   fresh_beans_26", False))
        lines.append(("", False))
        lines.append(("        THANK YOU FOR SHOPPING!", True))
        
    elif template_name == "grocery":
        lines.append(("   " + store_name, True))
        lines.append(("   " + store_addr, False))
        lines.append(("─" * 38, False))
        lines.append((f"   ST# {random.randint(100,999)} OP# {random.randint(10,99)} TE# {random.randint(1,99)}  TR# {receipt_no[:4]}", False))
        lines.append((f"   {date_str}", False))
        lines.append(("─" * 38, False))
        lines.append(("", False))
        
        for name, qty, price in items:
            # Multi-quantity sub-items
            if qty > 1:
                lines.append((f"   {name:<22}      {currency_symbol}{price:>6.2f}", False))
                lines.append((f"     {qty} @ {currency_symbol}{price/qty:.2f}", False))
            else:
                lines.append((f"   {name:<22}      {currency_symbol}{price:>6.2f}", False))
                
        lines.append(("", False))
        lines.append(("─" * 38, False))
        lines.append((f"   SUBTOTAL{'':14s}{currency_symbol}{subtotal:>6.2f}", False))
        lines.append((f"   TAX ({tax_rate*100:.1f}%){'':10s}{currency_symbol}{tax:>6.2f}", False))
        lines.append((f"   TOTAL{'':17s}{currency_symbol}{total:>6.2f}", True))
        lines.append(("─" * 38, False))
        lines.append((f"   DEBIT CARD: {card}", False))
        lines.append((f"   APP CODE: {auth_code}", False))
        lines.append(("", False))
        lines.append(("       * MEMBER SAVINGS APPLIED *", True))
        lines.append(("      Return Policy: 90 days with receipt", False))
        
    elif template_name == "retail":
        lines.append(("   " + store_name.upper(), True))
        lines.append(("   " + store_addr, False))
        lines.append(("", False))
        lines.append((f"   Receipt: {receipt_no}", False))
        lines.append((f"   Date: {date_str}", False))
        lines.append(("─" * 38, False))
        lines.append(("", False))
        
        for name, qty, price in items:
            lines.append((f"   {name:<24}", True))
            lines.append((f"     SKU_{random.randint(100000,999999)}    {qty:1d} x {currency_symbol}{price:.2f}", False))
            lines.append((f"     Item Total:        {currency_symbol}{price:>6.2f}", False))
            lines.append(("", False))
            
        lines.append(("─" * 38, False))
        lines.append((f"   Subtotal{'':14s}{currency_symbol}{subtotal:>6.2f}", False))
        lines.append((f"   Tax ({tax_rate*100:.1f}%){'':10s}{currency_symbol}{tax:>6.2f}", False))
        lines.append((f"   Total Amount{'':10s}{currency_symbol}{total:>6.2f}", True))
        lines.append(("─" * 38, False))
        lines.append((f"   Transaction Card: {card}", False))
        lines.append((f"   Approval Code: {auth_code}", False))
        lines.append(("", False))
        lines.append(("      NO RETURNS WITHOUT RECEIPT", True))
        lines.append(("    Thank you for choosing luxe.", False))
        
    else:  # gas
        lines.append(("   " + store_name, True))
        lines.append(("   " + store_addr, False))
        lines.append((f"   Tel: ({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}", False))
        lines.append(("─" * 38, False))
        lines.append((f"   Date: {date_str}", False))
        lines.append((f"   Pump: #{random.randint(1,24):02d}      Sale: {receipt_no}", False))
        lines.append(("─" * 38, False))
        lines.append(("", False))
        
        # First item is always fuel (different quantity type)
        fuel_name, fuel_gal, fuel_price = items[0]
        lines.append((f"   {fuel_name:<20} {currency_symbol}{fuel_price:>6.2f}", False))
        lines.append((f"     {fuel_gal} @ {currency_symbol}{fuel_price/float(fuel_gal.split()[0]):.3f}/G", False))
        
        # Rest of inside items
        for name, qty, price in items[1:]:
            lines.append((f"   {name:<22} {qty:1d}   {currency_symbol}{price:>6.2f}", False))
            
        lines.append(("", False))
        lines.append(("─" * 38, False))
        lines.append((f"   SUBTOTAL{'':14s}{currency_symbol}{subtotal:>6.2f}", False))
        lines.append((f"   TAX ({tax_rate*100:.1f}%){'':10s}{currency_symbol}{tax:>6.2f}", False))
        lines.append((f"   TOTAL{'':17s}{currency_symbol}{total:>6.2f}", True))
        lines.append(("─" * 38, False))
        lines.append((f"   CREDIT CARD: {card}", False))
        lines.append((f"   AUTH NO: {auth_code}", False))
        lines.append(("", False))
        lines.append(("     DRIVE SAFELY! COME BACK SOON!", True))
        
    # Measure total height needed
    font_reg = get_font(13, bold=False)
    font_bold = get_font(13, bold=True)
    
    line_h = 19
    padding = 35
    total_height = len(lines) * line_h + padding * 2
    
    # ─── Render Canvas ───
    canvas = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(canvas)
    
    y = padding
    for line_text, is_bold in lines:
        font = font_bold if (is_bold and font_style == "receipt") else font_reg
        draw.text((10, y), line_text, font=font, fill=text_color)
        y += line_h
        
    # Add subtle barcode at the bottom for authenticity (if grocery/cafe)
    if template_name in ["grocery", "cafe"] and total_height > 100:
        bar_y = total_height - 35
        bar_x = width // 2 - 70
        for i in range(40):
            w = random.choice([1, 2, 3, 4])
            color = text_color if random.choice([True, False]) else bg_color
            draw.rectangle([bar_x, bar_y, bar_x + w, bar_y + 14], fill=color)
            bar_x += w
            
    return canvas

# ─── Image Warping & Post-processing (Realism Filters) ───

def apply_thermal_effects(receipt_img, bg_color, text_color):
    """Applies thermal aging, text skew, print head fading, noise, and crop."""
    w, h = receipt_img.size
    
    # 1. Subtle horizontal jitter / print-head wobble
    # Slice the image into strips and shift them horizontally by 0 or 1 pixel
    jittered = Image.new("RGB", (w, h), bg_color)
    strip_h = random.randint(15, 30)
    for y in range(0, h, strip_h):
        offset = random.choice([-1, 0, 1])
        box = (0, y, w, min(y + strip_h, h))
        region = receipt_img.crop(box)
        jittered.paste(region, (offset, y))
    receipt_img = jittered
    
    # 2. Print head vertical fade lines (some spots have lower pressure/ink)
    fade_draw = ImageDraw.Draw(receipt_img, "RGBA")
    for _ in range(random.randint(1, 3)):
        fade_x = random.randint(20, w - 20)
        fade_w = random.randint(1, 3)
        fade_alpha = random.randint(15, 35)
        # Draw a semi-transparent band of the background paper color
        fade_draw.rectangle([fade_x, 0, fade_x + fade_w, h], fill=(*bg_color, fade_alpha))
        
    # 3. Horizontal line fade (faded ink on some lines)
    for _ in range(random.randint(1, 2)):
        fade_y = random.randint(40, h - 40)
        # Blend a slice of receipt with background paper color
        fade_h = random.randint(10, 25)
        strip = receipt_img.crop((0, fade_y, w, fade_y + fade_h))
        paper_strip = Image.new("RGB", (w, fade_h), bg_color)
        blended_strip = Image.blend(strip, paper_strip, random.uniform(0.15, 0.35))
        receipt_img.paste(blended_strip, (0, fade_y))

    # 4. Thermal paper yellowing/tinting (adds vintage feel if not overridden by reference)
    # Only apply if it's the default background color
    if bg_color == (245, 245, 240):
        r, g, b = receipt_img.split()
        r = r.point(lambda i: min(255, int(i * random.uniform(1.01, 1.05))))
        g = g.point(lambda i: min(255, int(i * random.uniform(0.97, 1.00))))
        b = b.point(lambda i: min(255, int(i * random.uniform(0.88, 0.94))))
        receipt_img = Image.merge("RGB", (r, g, b))

    # 5. Paper grain (noise overlay)
    noise = Image.effect_noise((w, h), random.randint(10, 22))
    noise_rgb = noise.convert("RGB")
    receipt_img = Image.blend(receipt_img, noise_rgb, random.uniform(0.04, 0.08))
    
    # 6. Micro rotation (0.2 - 0.7 deg) to look naturally cut
    angle = random.uniform(-0.6, 0.6)
    receipt_img = receipt_img.rotate(angle, expand=True, fillcolor=bg_color)
    
    # 7. Subtle edge blur (simulates camera lens soft focus)
    receipt_img = receipt_img.filter(ImageFilter.GaussianBlur(0.3))
    
    return receipt_img

def apply_tabletop_mode(receipt_img, bg_color, text_color):
    """Places the receipt onto a realistic textured background table with 3D warping and soft shadow."""
    rw, rh = receipt_img.size
    
    # Target size of the output image
    bg_w, bg_h = 580, max(rh + 140, 700)
    
    # 1. Select background style (wood or slate)
    bg_style = random.choice(["wood", "slate"])
    if bg_style == "wood":
        bg = generate_wood_background(bg_w, bg_h)
    else:
        bg = generate_slate_background(bg_w, bg_h)
        
    # 2. Draw 3D crease folds on the flat receipt first
    receipt_img = draw_3d_creases(receipt_img, bg_color, text_color)
    
    # 3. Create transparent canvas to hold the receipt and shadow
    overlay = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    
    # Calculate centering coordinates
    rx = (bg_w - rw) // 2
    ry = (bg_h - rh) // 2
    
    # Paste the receipt onto the overlay
    receipt_rgba = receipt_img.convert("RGBA")
    overlay.paste(receipt_rgba, (rx, ry))
    
    # 4. Generate perspective tilt / warp using Affine matrix (shear + translate)
    # We apply a slight skew (shear) in X and Y
    shear_x = random.uniform(-0.04, 0.04)
    shear_y = random.uniform(-0.03, 0.03)
    
    # Center-relative affine transformation matrix coefficients
    # x' = a*x + b*y + c
    # y' = d*x + e*y + f
    # To rotate/shear around the center (cx, cy):
    cx, cy = bg_w / 2, bg_h / 2
    a, b = 1.0, shear_x
    d, e = shear_y, 1.0
    c = cx - a * cx - b * cy
    f = cy - d * cx - e * cy
    
    warped_overlay = overlay.transform((bg_w, bg_h), Image.AFFINE, (a, b, c, d, e, f), Image.BICUBIC)
    
    # 5. Create drop shadow
    # Extract the alpha channel of the warped receipt
    alpha = warped_overlay.split()[3]
    
    # Create black shadow base
    shadow_base = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    # Fill the transparent silhouette with black (alpha-masked shadow)
    shadow_silhouette = Image.new("RGBA", (bg_w, bg_h), (12, 12, 12, 160)) # opacity 160
    shadow_base = Image.composite(shadow_silhouette, shadow_base, alpha)
    
    # Offset shadow (simulate directional light source coming from top-left)
    offset_x = random.randint(6, 12)
    offset_y = random.randint(10, 20)
    shadow_offset = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    shadow_offset.paste(shadow_base, (offset_x, offset_y))
    
    # Blur shadow heavily to make it soft
    shadow_soft = shadow_offset.filter(ImageFilter.GaussianBlur(radius=random.randint(12, 18)))
    
    # 6. Compose everything onto background
    bg = bg.convert("RGBA")
    # Paste shadow
    bg = Image.alpha_composite(bg, shadow_soft)
    # Paste warped receipt
    bg = Image.alpha_composite(bg, warped_overlay)
    
    # 7. Lighting adjustment: add global lighting gradient (simulates spotlight on table)
    light_gradient = Image.new("L", (bg_w, bg_h), 255)
    light_draw = ImageDraw.Draw(light_gradient)
    # Light center is slightly offset from receipt center
    lcx = random.randint(bg_w // 4, bg_w // 2)
    lcy = random.randint(bg_h // 4, bg_h // 2)
    for r in range(max(bg_w, bg_h), 0, -25):
        val = int(255 - (r / max(bg_w, bg_h)) * random.randint(25, 45))
        light_draw.ellipse([lcx - r, lcy - r, lcx + r, lcy + r], fill=val)
    light_gradient = light_gradient.filter(ImageFilter.GaussianBlur(35))
    
    # Create highlighted/shadowed overlay
    light_layer = Image.new("RGB", (bg_w, bg_h), (255, 255, 255))
    shaded_bg = Image.composite(bg.convert("RGB"), light_layer, light_gradient)
    
    # Final image crop to remove edges for a perfect photo look
    crop_padding = 10
    final_img = shaded_bg.crop((crop_padding, crop_padding, bg_w - crop_padding, bg_h - crop_padding))
    
    return final_img

# ─── Main Generation API ───

def generate_receipt_image(template="grocery", realism="tabletop", currency="USD", font="receipt", custom_style=None):
    """
    Core API to generate a receipt image.
    custom_style is an optional dict: {'bg_color': (R,G,B), 'text_color': (R,G,B)}
    """
    # 1. Colors Setup
    if custom_style:
        bg_color = custom_style.get("bg_color", (245, 245, 240))
        text_color = custom_style.get("text_color", (35, 35, 35))
    else:
        bg_color = (245, 245, 240)
        text_color = (35, 35, 35)
        
    # 2. Get currency metadata
    curr_symbol, _ = CURRENCIES.get(currency, ("$", "USD"))
    
    # 3. Generate random data pool
    data = get_receipt_data(template, curr_symbol)
    
    # 4. Render receipt text onto raw canvas
    img = draw_receipt_canvas(data, template, curr_symbol, font, bg_color, text_color)
    
    # 5. Apply realism filters
    if realism == "clean":
        # Returns perfectly centered digital style
        return img
    elif realism == "thermal":
        # Returns aged print receipt with transparent paper texture
        return apply_thermal_effects(img, bg_color, text_color)
    else:
        # Returns photorealistic tabletop layout
        # First thermal-ize it slightly so it doesn't look like a digital render on wood
        img_thermal = apply_thermal_effects(img, bg_color, text_color)
        return apply_tabletop_mode(img_thermal, bg_color, text_color)
