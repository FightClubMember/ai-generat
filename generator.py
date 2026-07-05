import os
import random
import string
import urllib.request
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Font Downloader ───
FONT_DIR = "fonts"
FONT_PATH = os.path.join(FONT_DIR, "RobotoMono-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "RobotoMono-Bold.ttf")

def download_fonts():
    """Downloads Roboto Mono from Google Fonts repository if not present."""
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
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
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

# ─── Restaurant Items Pool (Based exactly on reference image) ───

STORE_NAME = "ROYAL CHINESE GARDEN"
STORE_SUBTITLE = "(AUTHENTIC CHINESE CUISINE)"
STORE_ADDR = "Unit 3, LBS Marg, Ghatkopar West, Mumbai, Mumbai, India"
STORE_TEL = "022-25118877"
STORE_GSTIN = "27FFGGH7890P5Z2"
STORE_FOOTER = "THANK YOU VISIT AGAIN !!!"

CHINESE_ITEMS = [
    ("Mineral Water", 50.00),
    ("Lassi", 130.00),
    ("Malai Kofta", 380.00),
    ("Aloo Paratha", 160.00),
    ("Dal Makhani", 320.00),
    ("Fried Rice", 280.00),
    ("Chilli Paneer", 360.00),
    ("Veg Noodles", 240.00),
    ("Spring Roll", 180.00),
    ("Veg Manchurian", 260.00),
    ("Sweet Corn Soup", 140.00),
    ("Masala Papad", 60.00),
]

def random_date():
    d = datetime.now() - timedelta(days=random.randint(0, 15),
                                  hours=random.randint(0, 23),
                                  minutes=random.randint(0, 59))
    return d.strftime("%d/%m/%Y %H:%M")

def get_receipt_data():
    """Generates structured random data for the receipt, matching the reference image."""
    date_str = random_date()
    receipt_no = ''.join(random.choices(string.digits, k=4))
    
    items = []
    # Pick a random number of items (between 3 and 7)
    count = random.randint(3, 7)
    selected = random.sample(CHINESE_ITEMS, count)
    
    for name, u_price in selected:
        qty = random.choices([1, 2], weights=[80, 20])[0]
        price = round(u_price, 2)
        items.append((name, qty, price))
        
    subtotal = round(sum(q * p for _, q, p in items), 2)
    tax_rate = 0.05  # 5% total tax (2.5% CGST + 2.5% SGST)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    table_no = f"T{random.randint(1, 30):02d}"
    
    # Servers
    servers = ["Kiran", "Rahul", "Amit", "Pooja", "Sanjay", "Deepak", "Rohan"]
    server_name = random.choice(servers)
    
    return {
        "store_name": STORE_NAME,
        "subtitle": STORE_SUBTITLE,
        "store_addr": STORE_ADDR,
        "tel_no": STORE_TEL,
        "gstin": STORE_GSTIN,
        "date_str": date_str,
        "receipt_no": receipt_no,
        "items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
        "table_no": table_no,
        "server_name": server_name,
        "footer_msg": STORE_FOOTER
    }

# ─── Striped Tabletop Background ───

def generate_striped_background(width, height):
    """Generates the exact cream/beige vertical striped wallpaper background from the reference photo."""
    # Base warm cream/beige: #f2ede0 (242, 237, 224)
    bg = Image.new("RGB", (width, height), (242, 237, 224))
    draw = ImageDraw.Draw(bg)
    
    # Draw vertical stripes of slightly darker beige: #eae4d4 (234, 228, 212)
    stripe_w = 16
    for x in range(0, width, stripe_w * 2):
        draw.rectangle([x, 0, x + stripe_w, height], fill=(234, 228, 212))
        
    # Add very fine texture noise
    noise = Image.effect_noise((width, height), 6).convert("RGB")
    bg = Image.blend(bg, noise, 0.05)
    
    return bg

# ─── Crease/Fold Lines ───

def draw_3d_creases(receipt_img, bg_color, text_color):
    """Draws realistic highlight/shadow pairs to simulate 3D paper folds."""
    draw = ImageDraw.Draw(receipt_img, "RGBA")
    w, h = receipt_img.size
    
    highlight_color = (255, 255, 255, 20)  # semi-transparent white
    shadow_color = (0, 0, 0, 15)          # semi-transparent dark grey
        
    num_creases = random.randint(1, 3)
    for _ in range(num_creases):
        y_start = random.randint(h // 6, h * 5 // 6)
        y_end = y_start + random.randint(-40, 40)
        
        # Highlight line
        draw.line([-10, y_start, w + 10, y_end], fill=highlight_color, width=2)
        # Shadow line directly below it (1px offset)
        draw.line([-10, y_start + 1, w + 10, y_end + 1], fill=shadow_color, width=2)
        
    return receipt_img

# ─── Core Receipt Canvas Generator ───

def draw_receipt_canvas(data, bg_color, text_color):
    """Renders the receipt onto a canvas following the reference image structure exactly (42 chars wide)."""
    width = 380
    lines = [] # Array of tuples: (text_line, is_bold, is_large)
    
    # Local helper functions for exact character grid formatting (42 characters wide)
    def center_line(text):
        if len(text) >= 42:
            return text[:42]
        spaces = (42 - len(text)) // 2
        return " " * spaces + text
        
    store_name = data["store_name"]
    subtitle = data["subtitle"]
    store_addr = data["store_addr"]
    tel_no = data["tel_no"]
    gstin = data["gstin"]
    date_str = data["date_str"]
    receipt_no = data["receipt_no"]
    items = data["items"]
    subtotal = data["subtotal"]
    tax_rate = data["tax_rate"]
    tax = data["tax"]
    total = data["total"]
    table_no = data["table_no"]
    server_name = data["server_name"]
    footer_msg = data["footer_msg"]
    
    # ─── 1. Header Section (Center-aligned) ───
    lines.append((center_line(store_name.upper()), True, True))   # Large Bold Store Name
    lines.append((center_line(subtitle.upper()), True, False))   # Bold Subtitle
    # Draw address parts
    for part in store_addr.split(", "):
        lines.append((center_line(part), False, False))
    lines.append((center_line(f"Tel: {tel_no}"), False, False))
    lines.append((center_line(f"GSTIN: {gstin}"), False, False))
    
    lines.append(("------------------------------------------", False, False))
    
    # ─── 2. Metadata Grid ───
    date_part = date_str.split()[0]
    time_part = date_str.split()[1]
    
    left_1 = f"Date: {date_part}"
    left_2 = f"Time: {time_part}"
    left_3 = f"Server: {server_name}"
    
    right_1 = f"Table: {table_no}"
    right_2 = f"Bill: {receipt_no}"
    right_3 = f"Type: SALE"
    
    lines.append((f"{left_1:<21}{right_1}", False, False))
    lines.append((f"{left_2:<21}{right_2}", False, False))
    lines.append((f"{left_3:<21}{right_3}", False, False))
    
    lines.append(("------------------------------------------", False, False))
    
    # ─── 3. Table Header (Item, Qty, Price, Amount) ───
    table_header = f"{'Item':<16}{'Qty.':^8}{'Price':>9}{'Amount':>9}"
    lines.append((table_header, True, False))
    
    lines.append(("------------------------------------------", False, False))
    
    # ─── 4. Item Rows ───
    total_qty = 0
    for name, qty, price in items:
        qty_str = str(qty)
        amount = qty * price
        total_qty += qty
        
        name_fmt = name[:15]
        row = f"{name_fmt:<16}{qty_str:^8}{price:>9.2f}{amount:>9.2f}"
        lines.append((row, False, False))
        
    lines.append(("------------------------------------------", False, False))
    
    # ─── 5. Summary Section ───
    # Format Subtotal row
    qty_label = f"Total Qty: {total_qty}"
    subtotal_val = f"{'Sub Total:':<12}{subtotal:>9.2f}"
    lines.append((f"{qty_label:<21}{subtotal_val}", False, False))
    
    # GST splits (CGST 2.5% + SGST 2.5%)
    cgst_val = f"{'CGST 2.5%:':<12}{tax/2:>9.2f}"
    sgst_val = f"{'SGST 2.5%:':<12}{tax/2:>9.2f}"
    lines.append((f"{'':<21}{cgst_val}", False, False))
    lines.append((f"{'':<21}{sgst_val}", False, False))
        
    # Round off
    rounded_total = float(round(total))
    round_off = rounded_total - total
    round_val = f"{'Round off:':<12}{round_off:>9.2f}"
    lines.append((f"{'':<21}{round_val}", False, False))
    grand_total = rounded_total
        
    # Grand Total row (center-aligned bold)
    grand_str = f"Grand Total:  ₹ {grand_total:.2f}"
    lines.append((center_line(grand_str), True, False))
    
    lines.append(("------------------------------------------", False, False))
    
    # ─── 6. Footer message ───
    lines.append((center_line(footer_msg), True, False))
    lines.append(("------------------------------------------", False, False))
    
    # Measure total height needed dynamically based on font size
    font_reg = get_font(13, bold=False)
    font_bold = get_font(13, bold=True)
    font_large_bold = get_font(16, bold=True)
    
    line_h = 19
    padding = 35
    total_height = padding * 2
    
    for _, _, is_large in lines:
        total_height += 23 if is_large else line_h
        
    # Create image
    canvas = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(canvas)
    
    y = padding
    for line_text, is_bold, is_large in lines:
        if is_large:
            font = font_large_bold
            curr_line_h = 23
        else:
            font = font_bold if is_bold else font_reg
            curr_line_h = line_h
            
        draw.text((10, y), line_text, font=font, fill=text_color)
        y += curr_line_h
        
    return canvas

# ─── Image Warping & Post-processing (Realism Filters) ───

def apply_thermal_effects(receipt_img, bg_color, text_color):
    """Applies thermal aging, text skew, print head fading, noise, and crop."""
    w, h = receipt_img.size
    
    # 1. Subtle horizontal jitter / print-head wobble
    jittered = Image.new("RGB", (w, h), bg_color)
    strip_h = random.randint(15, 30)
    for y in range(0, h, strip_h):
        offset = random.choice([-1, 0, 1])
        box = (0, y, w, min(y + strip_h, h))
        region = receipt_img.crop(box)
        jittered.paste(region, (offset, y))
    receipt_img = jittered
    
    # 2. Print head vertical fade lines
    fade_draw = ImageDraw.Draw(receipt_img, "RGBA")
    for _ in range(random.randint(1, 3)):
        fade_x = random.randint(20, w - 20)
        fade_w = random.randint(1, 3)
        fade_alpha = random.randint(15, 35)
        fade_draw.rectangle([fade_x, 0, fade_x + fade_w, h], fill=(*bg_color, fade_alpha))
        
    # 3. Horizontal line fade
    for _ in range(random.randint(1, 2)):
        fade_y = random.randint(40, h - 40)
        fade_h = random.randint(10, 25)
        strip = receipt_img.crop((0, fade_y, w, fade_y + fade_h))
        paper_strip = Image.new("RGB", (w, fade_h), bg_color)
        blended_strip = Image.blend(strip, paper_strip, random.uniform(0.15, 0.35))
        receipt_img.paste(blended_strip, (0, fade_y))

    # 4. Vintage warm paper yellowing
    r, g, b = receipt_img.split()
    r = r.point(lambda i: min(255, int(i * random.uniform(1.01, 1.05))))
    g = g.point(lambda i: min(255, int(i * random.uniform(0.97, 1.00))))
    b = b.point(lambda i: min(255, int(i * random.uniform(0.88, 0.94))))
    receipt_img = Image.merge("RGB", (r, g, b))

    # 5. Paper grain noise
    noise = Image.effect_noise((w, h), random.randint(10, 22))
    noise_rgb = noise.convert("RGB")
    receipt_img = Image.blend(receipt_img, noise_rgb, random.uniform(0.04, 0.08))
    
    # 6. Micro rotation
    angle = random.uniform(-0.6, 0.6)
    receipt_img = receipt_img.rotate(angle, expand=True, fillcolor=bg_color)
    
    # 7. Subtle edge blur
    receipt_img = receipt_img.filter(ImageFilter.GaussianBlur(0.3))
    
    return receipt_img

def apply_tabletop_mode(receipt_img, bg_color, text_color):
    """Places the receipt onto the vertical striped background with 3D warping and soft shadow."""
    rw, rh = receipt_img.size
    bg_w, bg_h = 600, max(rh + 160, 720)
    
    # Generate the exact striped background from the reference photo
    bg = generate_striped_background(bg_w, bg_h)
        
    # Crease folds on flat receipt
    receipt_img = draw_3d_creases(receipt_img, bg_color, text_color)
    
    # Overlay transparent canvas
    overlay = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    rx = (bg_w - rw) // 2
    ry = (bg_h - rh) // 2
    receipt_rgba = receipt_img.convert("RGBA")
    overlay.paste(receipt_rgba, (rx, ry))
    
    # Perspective tilt / shear
    shear_x = random.uniform(-0.03, 0.03)
    shear_y = random.uniform(-0.02, 0.02)
    cx, cy = bg_w / 2, bg_h / 2
    a, b = 1.0, shear_x
    d, e = shear_y, 1.0
    c = cx - a * cx - b * cy
    f = cy - d * cx - e * cy
    
    warped_overlay = overlay.transform((bg_w, bg_h), Image.AFFINE, (a, b, c, d, e, f), Image.BICUBIC)
    
    # Drop shadow
    alpha = warped_overlay.split()[3]
    shadow_base = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    shadow_silhouette = Image.new("RGBA", (bg_w, bg_h), (12, 12, 12, 160))
    shadow_base = Image.composite(shadow_silhouette, shadow_base, alpha)
    
    offset_x = random.randint(6, 12)
    offset_y = random.randint(10, 20)
    shadow_offset = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    shadow_offset.paste(shadow_base, (offset_x, offset_y))
    
    shadow_soft = shadow_offset.filter(ImageFilter.GaussianBlur(radius=random.randint(12, 18)))
    
    # Blend together
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, shadow_soft)
    bg = Image.alpha_composite(bg, warped_overlay)
    
    # Global lighting gradient / vignette
    light_gradient = Image.new("L", (bg_w, bg_h), 255)
    light_draw = ImageDraw.Draw(light_gradient)
    lcx = random.randint(bg_w // 4, bg_w // 2)
    lcy = random.randint(bg_h // 4, bg_h // 2)
    for r in range(max(bg_w, bg_h), 0, -25):
        val = int(255 - (r / max(bg_w, bg_h)) * random.randint(25, 45))
        light_draw.ellipse([lcx - r, lcy - r, lcx + r, lcy + r], fill=val)
    light_gradient = light_gradient.filter(ImageFilter.GaussianBlur(35))
    
    light_layer = Image.new("RGB", (bg_w, bg_h), (255, 255, 255))
    shaded_bg = Image.composite(bg.convert("RGB"), light_layer, light_gradient)
    
    # Crop borders
    crop_padding = 10
    final_img = shaded_bg.crop((crop_padding, crop_padding, bg_w - crop_padding, bg_h - crop_padding))
    
    return final_img

# ─── Main Generation API ───

def generate_receipt_image():
    """
    Main API to generate a restaurant bill image matching the reference image.
    Always uses the Tabletop mode with the striped background and clean/thermal filters.
    """
    # Use exact colors from the reference photo
    bg_color = (245, 243, 237)  # Warm paper off-white
    text_color = (15, 15, 15)   # Charcoal print ink
    
    # 1. Generate receipt data
    data = get_receipt_data()
    
    # 2. Render text onto canvas
    img = draw_receipt_canvas(data, bg_color, text_color)
    
    # 3. Apply thermal aging effects
    img_thermal = apply_thermal_effects(img, bg_color, text_color)
    
    # 4. Place onto striped tabletop background with drop-shadow & tilt
    return apply_tabletop_mode(img_thermal, bg_color, text_color)
