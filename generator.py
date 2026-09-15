import os
import io
import json
import time
import random
import string
import urllib.request
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode

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

download_fonts()

def get_font(size, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

# ─── Barcode & Real Scannable QR Code Helpers ───

def draw_barcode(draw, x, y, width=280, height=50, seed_val=None):
    """Renders crisp vertical barcode lines (High DPI)."""
    if seed_val:
        random.seed(seed_val)
    curr_x = x
    while curr_x < x + width:
        w = random.choice([2, 3, 4, 5])
        draw.rectangle([curr_x, y, curr_x + w, y + height], fill=(15, 15, 15))
        curr_x += w + random.choice([2, 3, 4])

def draw_qr_code(canvas, x, y, size=140, data_str=None):
    """Pastes an authentic 100% real, scannable QR code at High DPI onto the canvas."""
    if not data_str:
        data_str = "https://pay.upi.gov.in/verify"
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(data_str)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((int(size), int(size)), Image.Resampling.NEAREST)
        canvas.paste(qr_img, (int(x), int(y)))
    except Exception as e:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([x, y, x + size, y + size], fill=(255, 255, 255), outline=(0, 0, 0), width=3)

# ─── Load Real Extracted Sample Assets ───

ASSETS_DIR = "assets"

def get_asset_image(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except Exception:
            pass
    return None

# ─── Standard Store Pools for Free Users ───

STORES_POOL = [
    {
        "name": "KFC (DEVYANI INTERNATIONAL LTD)",
        "subtitle": "(Medanta - The Medicity)",
        "address": "Sec-38, Gurgaon, Haryana",
        "city": "POS: Haryana",
        "tel": "FSSAI: 10617005000139",
        "gstin": "06AABCD5534A1Z9",
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU FOR VISITING KFC !!!",
        "layout_type": "grid",
        "items": [
            ("Indian Spicy Veg Rol", 213.50),
            ("ADDON REG FRIES & PEPSI", 145.00),
            ("Chana Burger DI/TA", 68.50),
            ("Zinger Burger", 189.00),
            ("Popcorn Chicken (L)", 249.00)
        ]
    },
    {
        "name": "BIGBASKET (INNOVATIVE RETAIL)",
        "subtitle": "(A TATA ENTERPRISE)",
        "address": "Khata No 97-1, Vill-Dundahera, Sec 22",
        "city": "Gurgaon, Haryana, 122016",
        "tel": "18601231000",
        "gstin": "06AACCI2053A1ZB",
        "separator": "=",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU FOR SHOPPING AT BIGBASKET",
        "layout_type": "grid",
        "items": [
            ("Sunfeast Dark Fantasy 108g", 30.00),
            ("Parle Happy Happy Choco 60g", 10.00),
            ("Brooke Bond Taaza Tea 250g", 60.00),
            ("Aashirvaad Atta 5kg", 265.00),
            ("Handling Charge", 8.00)
        ]
    }
]

def random_date():
    d = datetime.now() - timedelta(days=random.randint(0, 15),
                                  hours=random.randint(0, 23),
                                  minutes=random.randint(0, 59))
    return d.strftime("%d/%m/%Y %H:%M")

def get_receipt_data():
    """Generates structured random data selecting a random store from the pool."""
    store = random.choice(STORES_POOL)
    date_str = random_date()
    receipt_no = ''.join(random.choices(string.digits, k=4))
    
    items = []
    count = min(len(store["items"]), random.randint(3, 5))
    selected = random.sample(store["items"], count)
    
    for name, u_price in selected:
        qty = random.choices([1, 2], weights=[80, 20])[0]
        price = round(u_price, 2)
        items.append((name, qty, price))
        
    subtotal = round(sum(q * p for _, q, p in items), 2)
    tax_rate = store["tax_rate"]
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    table_no = f"T{random.randint(1, 30):02d}"
    servers = ["Kiran", "Rahul", "Amit", "Pooja", "Sanjay", "Deepak", "Rohan"]
    server_name = random.choice(servers)
    
    return {
        "store": store,
        "store_name": store["name"],
        "subtitle": store["subtitle"],
        "store_addr": f"{store['address']}, {store['city']}",
        "address_line1": store["address"],
        "address_line2": store["city"],
        "tel_no": store["tel"],
        "gstin": store["gstin"],
        "date_str": date_str,
        "receipt_no": receipt_no,
        "items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
        "table_no": table_no,
        "server_name": server_name,
        "footer_msg": store["footer"]
    }

# ─── Striped Tabletop Background ───

def generate_striped_background(width, height):
    """Generates the vertical striped beige background from the reference photo."""
    bg = Image.new("RGB", (width, height), (242, 237, 224))
    draw = ImageDraw.Draw(bg)
    
    stripe_w = 16
    for x in range(0, width, stripe_w * 2):
        draw.rectangle([x, 0, x + stripe_w, height], fill=(234, 228, 212))
        
    noise = Image.effect_noise((width, height), 6).convert("RGB")
    bg = Image.blend(bg, noise, 0.05)
    
    return bg

# ─── Core Receipt Canvas Generator ───

def draw_receipt_canvas(data, text_color):
    """Renders standard 3:4 POS receipts."""
    lines = []
    store = data["store"]
    store_name = data["store_name"]
    subtitle = data["subtitle"]
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
    
    sep_char = store.get("separator", "-")
    separator_line = sep_char * 42
    
    lines.append((store_name.upper(), True, True, True))
    lines.append((subtitle.upper(), True, False, True))
    lines.append((data["address_line1"], False, False, True))
    lines.append((data["address_line2"], False, False, True))
    lines.append((f"Tel: {tel_no}", False, False, True))
    
    if gstin:
        lines.append((f"GSTIN: {gstin}", False, False, True))
    
    lines.append((separator_line, False, False, False))
    
    date_part = date_str.split()[0]
    time_part = date_str.split()[1]
    
    layout_type = store.get("layout_type", "grid")
    
    if layout_type == "grid":
        left_1 = f"Date: {date_part}"
        left_2 = f"Time: {time_part}"
        left_3 = f"Server: {server_name}"
        
        right_1 = f"Table: {table_no}"
        right_2 = f"Bill: {receipt_no}"
        right_3 = f"Type: SALE"
        
        lines.append((f"{left_1:<21}{right_1}", False, False, False))
        lines.append((f"{left_2:<21}{right_2}", False, False, False))
        lines.append((f"{left_3:<21}{right_3}", False, False, False))
    else:
        lines.append((f"Date: {date_part}   Time: {time_part}", False, False, False))
        lines.append((f"Bill No: #{receipt_no}     Hub/Counter: {table_no}", False, False, False))
        lines.append((f"Cashier: {server_name}", False, False, False))
    
    lines.append((separator_line, False, False, False))
    
    table_header = f"{'Item':<16}{'Qty.':^8}{'Price':>9}{'Amount':>9}"
    lines.append((table_header, True, False, False))
    lines.append((separator_line, False, False, False))
    
    total_qty = 0
    for name, qty, price in items:
        qty_str = str(qty)
        amount = qty * price
        total_qty += qty
        
        name_fmt = name[:15]
        row = f"{name_fmt:<16}{qty_str:^8}{price:>9.2f}{amount:>9.2f}"
        lines.append((row, False, False, False))
        
    lines.append((separator_line, False, False, False))
    
    qty_label = f"Total Qty: {total_qty}"
    subtotal_val = f"{'Sub Total:':<12}{subtotal:>9.2f}"
    lines.append((f"{qty_label:<21}{subtotal_val}", False, False, False))
    
    if store.get("has_gst", True) and tax > 0:
        cgst_val = f"{f'CGST {tax_rate*100/2:.1f}%:':<12}{tax/2:>9.2f}"
        sgst_val = f"{f'SGST {tax_rate*100/2:.1f}%:':<12}{tax/2:>9.2f}"
        lines.append((f"{'':<21}{cgst_val}", False, False, False))
        lines.append((f"{'':<21}{sgst_val}", False, False, False))
        
        rounded_total = float(round(total))
        round_off = rounded_total - total
        round_val = f"{'Round off:':<12}{round_off:>9.2f}"
        lines.append((f"{'':<21}{round_val}", False, False, False))
        grand_total = rounded_total
    else:
        grand_total = subtotal
        
    grand_str = f"Grand Total:  ₹ {grand_total:.2f}"
    lines.append((grand_str, True, False, True))
    lines.append((separator_line, False, False, False))
    lines.append((footer_msg, True, False, True))
    lines.append((separator_line, False, False, False))
    
    font_reg = get_font(13, bold=False)
    font_bold = get_font(13, bold=True)
    font_large_bold = get_font(16, bold=True)
    
    line_h = 19
    padding = 35
    total_height = padding * 2
    
    for _, _, is_large, _ in lines:
        total_height += 23 if is_large else line_h
        
    width = total_height * 3 // 4
    canvas = generate_striped_background(width, total_height)
    draw = ImageDraw.Draw(canvas)
    x_offset = max(10, (width - 336) // 2)
    
    y = padding
    for line_text, is_bold, is_large, is_centered in lines:
        if is_large:
            font = font_large_bold
            curr_line_h = 23
        else:
            font = font_bold if is_bold else font_reg
            curr_line_h = line_h
            
        if is_centered:
            text_w = draw.textlength(line_text, font=font)
            x = (width - text_w) // 2
            draw.text((x, y), line_text, font=font, fill=text_color)
        else:
            draw.text((x_offset, y), line_text, font=font, fill=text_color)
            
        y += curr_line_h
        
    return canvas

# ─── 👑 ADMIN 100% PERFECT EXACT SAMPLE REPLICAS ───

KFC_MENU = [
    ("Indian Spicy Veg Rol", 213.50),
    ("ADDON REG FRIES & PEPSI", 145.00),
    ("Chana Burger DI/TA", 128.50),
    ("Zinger Burger", 189.00),
    ("Popcorn Chicken (L)", 249.00),
    ("Hot & Crispy 2Pcs", 229.00),
    ("Veg Zinger Meal", 299.00),
    ("Pepsi Can 330ml", 60.00),
    ("Krushers Chocolate", 119.00),
    ("Choco Mud Pie", 109.00),
    ("Peri Peri Strips 3Pcs", 159.00),
    ("Chicken Bucket 4Pcs", 499.00),
    ("Ultimate Bucket 8Pcs", 799.00),
    ("Mingles Bucket", 369.00)
]

KFC_LOCATIONS = [
    ("Medanta - The Medicity", "Sec-38, Gurgaon(Haryana)"),
    ("DLF CyberHub", "DLF Phase 2, Gurgaon(Haryana)"),
    ("Connaught Place", "Inner Circle, New Delhi"),
    ("Sector 18 Market", "Block K, Noida(UP)"),
    ("Phoenix Marketcity", "Kurla West, Mumbai(Maharashtra)")
]

def generate_kfc_exact_replica_receipt(custom_address=None, custom_name=None):
    """
    Renders a 100% EXACT visual replica of the KFC thermal receipt photo (IMG_20260915_074530_315.jpg)
    matching font, alignment, spacing, token format, border margins, red side logos, and real QR code.
    """
    scale = 2
    width = 460 * scale
    
    if custom_address:
        loc = ("KFC Express Branch", custom_address)
    else:
        loc = random.choice(KFC_LOCATIONS)
        
    d = datetime.now() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    date_str = d.strftime("%d-%m-%y %H:%M")
    
    inv_no = f"9130{''.join(random.choices(string.digits, k=6))}"
    ord_no = f"3492{''.join(random.choices(string.digits, k=9))}"
    pos_no = f"T{''.join(random.choices(string.digits, k=5))}"
    token_no = f"{random.randint(100, 999):04d}"
    card_last4 = f"{random.randint(1000, 9999)}"
    card_brand = random.choice(["Plutus Card", "HDFC Card", "ICICI Card", "Axis Card", "Paytm Card"])
    
    while True:
        selected_items = random.sample(KFC_MENU, random.randint(3, 5))
        item_rows = []
        for name, price in selected_items:
            qty = random.choice([1, 2])
            disc = random.choice([0.00, 0.00, 15.00])
            amt = round((price * qty) - disc, 2)
            subs = []
            if "ADDON" in name:
                subs = ["  FRIES-REGULAR       1", "  PEPSI -REG          1"]
            item_rows.append((name, price, qty, disc, amt, subs))
            
        subtotal = round(sum(x[4] for x in item_rows), 2)
        sgst = round(subtotal * 0.025, 2)
        cgst = round(subtotal * 0.025, 2)
        total = round(subtotal + sgst + cgst, 2)
        if total >= 520.0:
            break
            
    lines = []
    lines.append(("KFC,", True, True, True))
    lines.append(("Devyani International Ltd.", True, False, True))
    lines.append((loc[0], False, False, True))
    
    addr_str = loc[1]
    if len(addr_str) > 34:
        lines.append((addr_str[:34], False, False, True))
        lines.append((addr_str[34:68], False, False, True))
    else:
        lines.append((addr_str, False, False, True))
        
    lines.append(("POS: Haryana", False, False, True))
    lines.append(("GSTIN No.: 06AABCD5534A1Z9", False, False, True))
    lines.append(("Service Code Tariff: 996331", False, False, True))
    lines.append(("FSSAI No.: 10617005000139", False, False, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append(("INVOICE", True, False, True))
    lines.append((f"Inv No {inv_no}  ORD No  {ord_no[:10]}", False, False, False))
    lines.append((f"Date:  {date_str}  POS No.     {pos_no}", False, False, False))
    lines.append((f"Token No:- {token_no}", True, True, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append(("*DINE-IN*", True, True, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append((f"{'Description':<14} {'Price':>8} {'Qty':>3} {'Disc.':>5} {'Amount':>8}", True, False, False))
    lines.append(("---------------------------------------", False, False, True))
    
    for name, price, qty, disc, amt, subs in item_rows:
        lines.append((name, False, False, False))
        disc_str = f"{disc:.2f}" if disc > 0 else "0.00"
        lines.append((f"{price:>21.2f} {qty:>3} {disc_str:>5} {amt:>8.2f}", False, False, False))
        for sub in subs:
            lines.append((sub, False, False, False))
            
    lines.append(("---------------------------------------", False, False, True))
    lines.append((f"{'Total Amount (Before Tax)':<26} {subtotal:>10.2f}", False, False, False))
    lines.append((f"{'SGST @ 2.5%':<26} {sgst:>10.2f}", False, False, False))
    lines.append((f"{'CGST @ 2.5%':<26} {cgst:>10.2f}", False, False, False))
    lines.append((f"{'Gross Amount':<26} {total:>10.2f}", True, False, False))
    lines.append((f"{'Bill Amount':<26} {total:>10.2f}", True, False, False))
    lines.append(("---------------------------------------", False, False, True))
    lines.append(("Payments:", True, False, False))
    lines.append((f"{card_brand:<26} {total:>10.2f}", False, False, False))
    lines.append((f" {card_last4}", False, False, False))
    lines.append(("---------------------------------------", False, False, True))
    lines.append((f"{'Payments:':<26} {total:>10.2f}", False, False, False))
    lines.append(("---------------------------------------", False, False, True))
    
    font_reg = get_font(13 * scale, bold=False)
    font_bold = get_font(13 * scale, bold=True)
    font_large_bold = get_font(17 * scale, bold=True)
    font_kfc = get_font(15 * scale, bold=True)
    
    line_h = 20 * scale
    padding = 30 * scale
    total_height = padding * 2 + (110 * scale)
    
    for _, _, is_large, _ in lines:
        total_height += (24 * scale) if is_large else line_h
        
    canvas = Image.new("RGB", (width, total_height), (246, 246, 243))
    draw = ImageDraw.Draw(canvas)
    
    # Draw Vertical Red KFC Side Border Logos (High DPI)
    red_color = (195, 16, 40)
    for y_pos in range(30 * scale, total_height - (70 * scale), 110 * scale):
        draw.text((12 * scale, y_pos), "KFC", font=font_kfc, fill=red_color)
        draw.text((width - (50 * scale), y_pos), "KFC", font=font_kfc, fill=red_color)
        
    y = padding
    text_color = (18, 18, 18)
    x_left = 60 * scale
    
    for line_text, is_bold, is_large, is_centered in lines:
        if is_large:
            font = font_large_bold
            curr_line_h = 24 * scale
        else:
            font = font_bold if is_bold else font_reg
            curr_line_h = line_h
            
        if is_centered:
            text_w = draw.textlength(line_text, font=font)
            x = (width - text_w) // 2
            draw.text((x, y), line_text, font=font, fill=text_color)
        else:
            draw.text((x_left, y), line_text, font=font, fill=text_color)
            
        y += curr_line_h
        
    # Draw real scannable bottom QR code
    draw_qr_code(canvas, (width - (100 * scale)) // 2, y + (10 * scale), size=100 * scale, data_str=f"https://pay.kfc.in/receipt/{inv_no}")
    
    data_summary = {
        "store_name": f"KFC ({loc[0]})",
        "store_addr": f"{loc[1]}",
        "total": total
    }
    return canvas, data_summary

BB_ITEMS_CATALOG = [
    ("Sunfeast Dark Fantasy Bourbon 108g", "19053290", 30.00, 15.00, 15.08, 0.83, 15.08),
    ("Parle Happy Happy Choco Cookies 60g", "19053290", 10.00, 0.00, 10.00, 0.48, 10.00),
    ("Brooke Bond Taaza Tea Leaf 250g", "09024090", 60.00, 0.00, 60.00, 2.86, 60.00),
    ("Aashirvaad Shuddh Chakki Atta 5kg", "11010000", 265.00, 20.00, 245.00, 11.67, 245.00),
    ("Fortune Kachi Ghani Mustard Oil 1L", "15149010", 160.00, 15.00, 145.00, 6.90, 145.00),
    ("Tata Salt Lite Low Sodium 1kg", "25010010", 32.00, 3.00, 29.00, 1.38, 29.00),
    ("Surf Excel Easy Wash Detergent 1kg", "34022010", 145.00, 10.00, 135.00, 6.43, 135.00),
    ("Amul Pasteurised Butter 500g Pack", "04051000", 275.00, 15.00, 260.00, 12.38, 260.00),
    ("Maggi 2-Minute Masala 12-Pack", "19023010", 168.00, 18.00, 150.00, 7.14, 150.00),
    ("Good Life Pure Refined Sugar 5kg", "17019990", 240.00, 20.00, 220.00, 10.48, 220.00),
    ("Ferrero Rocher Chocolate 16 Pcs", "18069010", 899.00, 100.00, 799.00, 38.05, 799.00),
    ("Nestle Everyday Dairy Whitener 1kg", "04029110", 520.00, 45.00, 475.00, 22.62, 475.00)
]

CUSTOMER_POOL = [
    ("Arbind Singh", "near Kanak public School, Kapas Hera Extension, Delhi (07)"),
    ("Rahul Sharma", "Flat 402, DLF Phase 3, Gurugram, Haryana (06)"),
    ("Priya Patel", "Tower B, Hiranandani Gardens, Powai, Mumbai (27)"),
    ("Amit Kumar", "Sector 62, Near Metro Station, Noida (09)"),
    ("Deepak Verma", "HSR Layout Sector 3, Bengaluru, Karnataka (29)"),
    ("Sanjay Gupta", "Civil Lines, Near Circuit House, Jaipur (08)")
]

def generate_bigbasket_exact_replica_invoice(custom_address=None, custom_name=None):
    """
    Renders a 100% EXACT visual replica of BigBasket Tax Invoice PDF (Invoice_from_bb_2100479625.pdf)
    matching exact column structure, fonts, top banner, supplier/customer grid, exact table headers,
    extracted logo, and exact blue ink signature.
    """
    scale = 3 # 3X High DPI for 100% vector-crisp match (2550x3300 resolution)
    width = 850 * scale
    height = 1100 * scale
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    if custom_address:
        c_name = custom_name if custom_name else "Arbind Singh"
        cust = (c_name, custom_address)
    else:
        cust = random.choice(CUSTOMER_POOL)
        
    inv_num = f"IEXHR26I{''.join(random.choices(string.digits, k=5))}"
    d = datetime.now() - timedelta(days=random.randint(0, 10))
    inv_date = d.strftime("%Y-%m-%d")
    ord_num = f"EXN-{random.randint(1000000, 9999999)}-{d.strftime('%Y%m%d')}"
    slot_str = f"{d.strftime('%a %d %b %Y')} between 10:00 AM and 11:00 AM"
    
    font_reg = get_font(9 * scale, bold=False)
    font_bold = get_font(9 * scale, bold=True)
    font_small = get_font(8 * scale, bold=False)
    font_small_bold = get_font(8 * scale, bold=True)
    font_large_bold = get_font(14 * scale, bold=True)
    
    # 1. Red Header Banner (Exact PDF Top Bar)
    red_bg = (195, 25, 30)
    draw.rectangle([0, 0, width, 30 * scale], fill=red_bg)
    draw.text((width // 2 - (70 * scale), 8 * scale), "Original  Tax  Invoice", font=font_large_bold, fill=(255, 255, 255))
    
    # 2. Paste Real BigBasket Logo
    logo_img = get_asset_image("bb_logo_real.png")
    if logo_img:
        logo_w, logo_h = logo_img.size
        target_w = int(140 * scale)
        target_h = int(logo_h * (target_w / logo_w))
        logo_resized = logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        canvas.paste(logo_resized, (35 * scale, 35 * scale), logo_resized)
    else:
        draw.text((35 * scale, 38 * scale), "bb", font=get_font(18 * scale, bold=True), fill=(110, 180, 40))
        draw.text((70 * scale, 42 * scale), "bigbasket", font=font_large_bold, fill=(20, 20, 20))
        draw.text((70 * scale, 58 * scale), "A TATA Enterprise", font=font_small_bold, fill=(0, 70, 150))
        
    # 3. Top Info Grid Boxes (Exact PDF Lines & Coordinates)
    # Outer Frame Grid Box
    grid_top = 80 * scale
    grid_bottom = 260 * scale
    draw.rectangle([35 * scale, grid_top, 815 * scale, grid_bottom], outline=(200, 200, 200), width=scale)
    draw.line([(310 * scale, grid_top), (310 * scale, grid_bottom)], fill=(200, 200, 200), width=scale)
    draw.line([(550 * scale, grid_top), (550 * scale, grid_bottom)], fill=(200, 200, 200), width=scale)
    
    # Column 1: Supplier Info
    draw.text((45 * scale, 90 * scale), "Details of Supplier", font=font_bold, fill=(30, 30, 30))
    draw.text((45 * scale, 110 * scale), "Innovative Retail Concepts Pvt Ltd, Khata No 97-1,", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 126 * scale), "Vill-Dundahera, Sector 22, Gurgaon, 122016", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 142 * scale), "Tel: 18601231000", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 158 * scale), "GSTIN: 06AACCI2053A1ZB", font=font_bold, fill=(30, 30, 30))
    draw.text((45 * scale, 174 * scale), "CIN: U74130KA2010PTC052192", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 190 * scale), "FSSAI Lic No: 10824005001463", font=font_reg, fill=(30, 30, 30))
    
    # Column 2: Bill to / Ship to
    draw.text((320 * scale, 90 * scale), "Bill to/Ship to:", font=font_bold, fill=(30, 30, 30))
    draw.text((320 * scale, 110 * scale), cust[0], font=font_bold, fill=(30, 30, 30))
    
    addr1 = cust[1][:34] if len(cust[1]) > 34 else cust[1]
    addr2 = cust[1][34:68] if len(cust[1]) > 34 else ""
    draw.text((320 * scale, 126 * scale), addr1, font=font_reg, fill=(30, 30, 30))
    draw.text((320 * scale, 142 * scale), addr2, font=font_reg, fill=(30, 30, 30))
    
    # Column 3: Invoice Info Table
    draw.text((560 * scale, 90 * scale), f"Invoice Number", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 90 * scale), f"{inv_num}", font=font_bold, fill=(30, 30, 30))
    
    draw.text((560 * scale, 110 * scale), f"Invoice Date", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 110 * scale), f"{inv_date}", font=font_reg, fill=(30, 30, 30))
    
    draw.line([(550 * scale, 130 * scale), (815 * scale, 130 * scale)], fill=(220, 220, 220), width=1)
    
    draw.text((560 * scale, 140 * scale), f"Order No", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 140 * scale), f"{ord_num[:20]}", font=font_reg, fill=(30, 30, 30))
    
    draw.text((560 * scale, 160 * scale), f"Payable Amount", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 160 * scale), f"Rs. 0.00", font=font_bold, fill=(30, 30, 30))
    
    draw.text((560 * scale, 180 * scale), f"Payment Mode", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 180 * scale), f"walletPrepaid", font=font_reg, fill=(30, 30, 30))
    
    draw.text((560 * scale, 200 * scale), f"Source", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 200 * scale), f"bb-b2c", font=font_reg, fill=(30, 30, 30))
    
    draw.text((560 * scale, 220 * scale), f"No. of Items", font=font_reg, fill=(80, 80, 80))
    draw.text((680 * scale, 220 * scale), f"3", font=font_reg, fill=(30, 30, 30))
    
    # 4. Exact Table Grid Header (Matching Sample PDF 12 Columns)
    tbl_top = 280 * scale
    tbl_hdr_h = 28 * scale
    draw.rectangle([35 * scale, tbl_top, 815 * scale, tbl_top + tbl_hdr_h], fill=(235, 235, 235), outline=(180, 180, 180))
    
    col_x = [38, 55, 180, 240, 275, 320, 370, 420, 475, 520, 600, 680, 750]
    headers = [
        "SI No.", "Item Description", "HSN Code", "Qty", "Unit Price",
        "Unit Taxable", "Gross Val", "Discount", "Other Chg", "Taxable Val", "IGST Amt", "TOTAL"
    ]
    
    for i, h in enumerate(headers):
        draw.text((col_x[i] * scale, tbl_top + (6 * scale)), h, font=font_small_bold, fill=(20, 20, 20))
        
    while True:
        selected = random.sample(BB_ITEMS_CATALOG, 3)
        item_rows = []
        subtotal_val = 0.0
        total_savings = 0.0
        for desc, hsn, u_price, disc, taxable, tax_val, tot_val in selected:
            qty = 1
            gross = u_price * qty
            tot = round(gross - disc, 2)
            subtotal_val += tot
            total_savings += disc
            item_rows.append((desc, hsn, qty, u_price, taxable, gross, disc, tax_val, tot))
            
        handling_fee = 8.00
        subtotal_val += handling_fee
        if subtotal_val >= 600.0:
            break

    y_tbl = tbl_top + tbl_hdr_h
    sno = 1
    for desc, hsn, qty, u_price, taxable, gross, disc, tax_val, tot in item_rows:
        draw.text((col_x[0] * scale, y_tbl + (8 * scale)), str(sno), font=font_small, fill=(30, 30, 30))
        draw.text((col_x[1] * scale, y_tbl + (8 * scale)), desc[:24], font=font_small, fill=(30, 30, 30))
        draw.text((col_x[2] * scale, y_tbl + (8 * scale)), hsn, font=font_small, fill=(30, 30, 30))
        draw.text((col_x[3] * scale, y_tbl + (8 * scale)), str(qty), font=font_small, fill=(30, 30, 30))
        draw.text((col_x[4] * scale, y_tbl + (8 * scale)), f"{u_price:.2f}", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[5] * scale, y_tbl + (8 * scale)), f"{taxable:.2f}", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[6] * scale, y_tbl + (8 * scale)), f"{gross:.2f}", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[7] * scale, y_tbl + (8 * scale)), f"{disc:.2f}", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[8] * scale, y_tbl + (8 * scale)), "0.00", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[9] * scale, y_tbl + (8 * scale)), f"{taxable:.2f}", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[10] * scale, y_tbl + (8 * scale)), "5.00%", font=font_small, fill=(30, 30, 30))
        draw.text((col_x[11] * scale, y_tbl + (8 * scale)), f"{tot:.2f}", font=font_small, fill=(30, 30, 30))
        
        y_tbl += 32 * scale
        draw.line([(35 * scale, y_tbl), (815 * scale, y_tbl)], fill=(240, 240, 240))
        sno += 1
        
    # Handling charge row
    draw.text((col_x[1] * scale, y_tbl + (8 * scale)), "Handling Charge", font=font_small, fill=(30, 30, 30))
    draw.text((col_x[11] * scale, y_tbl + (8 * scale)), f"Rs.{handling_fee:.2f}", font=font_small, fill=(30, 30, 30))
    y_tbl += 32 * scale
    
    # 5. GST Summary & Right Summary Boxes (Exact Sample Match)
    y_sum = y_tbl + (20 * scale)
    draw.rectangle([35 * scale, y_sum, 380 * scale, y_sum + (110 * scale)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((45 * scale, y_sum + (10 * scale)), "GST Information", font=font_bold, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (30 * scale)), "IGST Rate: 5.00%", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (50 * scale)), f"Taxable Value: Rs. {subtotal_val*0.95:.2f}", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (70 * scale)), f"Tax Value: Rs. {subtotal_val*0.05:.2f}", font=font_reg, fill=(30, 30, 30))
    
    # QR Code inside GST Box
    draw_qr_code(canvas, 290 * scale, y_sum + (10 * scale), size=80 * scale, data_str=f"https://www.bigbasket.com/invoice/verify/{inv_num}")
    
    # Summary Box Right
    draw.rectangle([400 * scale, y_sum, 815 * scale, y_sum + (140 * scale)], fill=(250, 250, 250), outline=(190, 190, 190))
    draw.text((410 * scale, y_sum + (10 * scale)), "Sub Total:", font=font_bold, fill=(30, 30, 30))
    draw.text((680 * scale, y_sum + (10 * scale)), f"Rs. {subtotal_val:.2f}", font=font_bold, fill=(30, 30, 30))
    
    draw.text((410 * scale, y_sum + (35 * scale)), "Debit availed from Wallet:", font=font_reg, fill=(60, 60, 60))
    draw.text((680 * scale, y_sum + (35 * scale)), f"Rs. {subtotal_val:.2f}", font=font_reg, fill=(60, 60, 60))
    
    draw.text((410 * scale, y_sum + (60 * scale)), "You Saved:", font=font_bold, fill=(40, 150, 40))
    draw.text((680 * scale, y_sum + (60 * scale)), f"Rs. {total_savings:.2f}", font=font_bold, fill=(40, 150, 40))
    
    draw.text((410 * scale, y_sum + (85 * scale)), "Total Invoice Value:", font=font_bold, fill=(195, 25, 30))
    draw.text((680 * scale, y_sum + (85 * scale)), f"Rs. {subtotal_val:.2f}", font=font_bold, fill=(195, 25, 30))
    
    # 6. Paste Real Signature
    sig_img = get_asset_image("bb_signature_real.png")
    if sig_img:
        sig_w, sig_h = sig_img.size
        target_w = int(220 * scale)
        target_h = int(sig_h * (target_w / sig_w))
        sig_resized = sig_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        canvas.paste(sig_resized, (560 * scale, y_sum + (150 * scale)), sig_resized)
    else:
        draw.text((570 * scale, y_sum + (180 * scale)), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
        
    draw.text((565 * scale, y_sum + (250 * scale)), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
    data_summary = {
        "store_name": "BIGBASKET (A TATA Enterprise)",
        "store_addr": f"Delivered to {cust[0]} ({cust[1][:25]})",
        "total": subtotal_val
    }
    return canvas, data_summary

LK_ITEMS_CATALOG = [
    ("Transparent Full Rim Square Lenskart Air", "Comfort LA E15019-C3 Eyeglasses", 3500.00, 500.00),
    ("Vincent Chase Air Flex Matte Black", "Full Rim Square Eyeglasses E12001", 2800.00, 400.00),
    ("John Jacobs Acetate Premium Gold Frame", "Square Polarized Eyeglasses JJ E1192", 5500.00, 800.00),
    ("Ray-Ban Aviator Metal Frame Classic", "Gold Legend Series Sunglasses RB3025", 8990.00, 1000.00),
    ("Lenskart BLU Thin Anti-Glare Lens", "Zero Power High Index Blu Cut Lens", 2200.00, 300.00),
    ("Lenskart Progressive Supreme Lens", "Multi-Focal Anti-Reflective Optical Lens", 6800.00, 900.00),
    ("Aqualens 24H Premium Contact Lenses", "Monthly Disposable Soft Lenses (6 Pcs)", 2400.00, 350.00)
]

def generate_lenskart_exact_replica_invoice(custom_address=None, custom_name=None):
    """
    Renders a 100% EXACT visual replica of Lenskart Tax Invoice PDF (Invoice_1348995593 (1).pdf)
    matching exact column structure, header grid, barcodes, customer address boxes, disclaimers,
    extracted logo, and exact extracted blue ink signature.
    """
    scale = 3 # 3X High DPI for 100% vector-crisp match (2550x3300 resolution)
    width = 850 * scale
    height = 1100 * scale
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    if custom_address:
        c_name = custom_name if custom_name else "Arbind Singh"
        cust = (c_name, custom_address)
    else:
        cust = random.choice(CUSTOMER_POOL)
        
    shipment_code = f"SNXS12700000075{''.join(random.choices(string.digits, k=5))}"
    order_id = f"1348995{''.join(random.choices(string.digits, k=3))}"
    inv_no = f"IIN10826B{''.join(random.choices(string.digits, k=6))}"
    
    font_reg = get_font(9 * scale, bold=False)
    font_bold = get_font(9 * scale, bold=True)
    font_small = get_font(8 * scale, bold=False)
    font_large = get_font(14 * scale, bold=True)
    
    # Outer Border Box
    draw.rectangle([30 * scale, 30 * scale, width - (30 * scale), height - (30 * scale)], outline=(0, 0, 0), width=2*scale)
    
    # 1. Top Title Banner
    draw.text((width // 2 - (40 * scale), 40 * scale), "Tax Invoice", font=font_large, fill=(0, 0, 0))
    draw.line([(30 * scale, 65 * scale), (width - (30 * scale), 65 * scale)], fill=(0, 0, 0), width=2*scale)
    
    # 2. Header Grid 3 Columns (Matching Sample PDF)
    # Left Column Header
    draw.text((40 * scale, 75 * scale), f"Shipment Code : # ", font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 90 * scale), f"{shipment_code[:18]}", font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 108 * scale), f"Order : # {order_id}", font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 124 * scale), "Order Date: 20/08/2026", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 40 * scale, 142 * scale, width=150 * scale, height=30 * scale, seed_val=int(order_id))
    draw.text((40 * scale, 180 * scale), f"Invoice:# {inv_no}", font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 196 * scale), "Invoice Date: 21/08/2026", font=font_reg, fill=(0, 0, 0))
    
    # Middle Column Header (Lenskart Details + Paste Real Header Logo)
    draw.line([(240 * scale, 65 * scale), (240 * scale, 230 * scale)], fill=(0, 0, 0), width=2*scale)
    
    logo_hdr = get_asset_image("lk_header_logo.png")
    if logo_hdr:
        lw, lh = logo_hdr.size
        tw = int(180 * scale)
        th = int(lh * (tw / lw))
        logo_resized = logo_hdr.resize((tw, th), Image.Resampling.LANCZOS)
        canvas.paste(logo_resized, (250 * scale, 70 * scale), logo_resized)
    else:
        draw.text((250 * scale, 75 * scale), "Lenskart Solutions Limited", font=font_bold, fill=(0, 0, 0))
        
    draw.text((250 * scale, 125 * scale), "(formerly known as Lenskart Solutions Private Limited)", font=font_small, fill=(50, 50, 50))
    draw.text((250 * scale, 140 * scale), "Reg. Office: Plot No. 151, Okhla Industrial Estate, Phase III, New Delhi, 110020", font=font_small, fill=(0, 0, 0))
    draw.text((250 * scale, 154 * scale), "Contact Email : support@lenskart.com", font=font_small, fill=(0, 0, 0))
    draw.text((250 * scale, 168 * scale), "CIN: L33100DL2008PLC178355 | GSTIN: 08AACCV7324B1ZK", font=font_small, fill=(0, 0, 0))
    draw.text((250 * scale, 182 * scale), "Supplier address: Industrial Plot SP-9, Bhiwadi, Rajasthan", font=font_small, fill=(0, 0, 0))
    draw.text((250 * scale, 196 * scale), "www.lenskart.com | 9999899998 (9 AM - 8 PM)", font=font_small, fill=(0, 0, 0))
    
    # Right Column Header
    draw.line([(570 * scale, 65 * scale), (570 * scale, 230 * scale)], fill=(0, 0, 0), width=2*scale)
    draw.text((620 * scale, 75 * scale), f"{random.randint(90000, 99999)}", font=font_large, fill=(0, 0, 0))
    draw.text((580 * scale, 98 * scale), "Shipment Code:", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 580 * scale, 115 * scale, width=150 * scale, height=30 * scale, seed_val=int(shipment_code[14:]))
    draw.text((580 * scale, 155 * scale), "Payment Method: PREPAID", font=font_bold, fill=(0, 0, 0))
    draw.text((580 * scale, 172 * scale), "Order Type: 1", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 230 * scale), (width - (30 * scale), 230 * scale)], fill=(0, 0, 0), width=2*scale)
    
    # 3. Addresses Boxes
    draw.text((40 * scale, 240 * scale), "Bill To Address", font=font_bold, fill=(0, 0, 0))
    draw.text((320 * scale, 240 * scale), "Address Of Delivery", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40 * scale, 260 * scale), cust[0], font=font_bold, fill=(0, 0, 0))
    addr_l1 = cust[1][:34] if len(cust[1]) > 34 else cust[1]
    addr_l2 = cust[1][34:68] if len(cust[1]) > 34 else ""
    
    draw.text((40 * scale, 276 * scale), addr_l1, font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 292 * scale), addr_l2, font=font_reg, fill=(0, 0, 0))
    
    draw.text((320 * scale, 260 * scale), cust[0], font=font_bold, fill=(0, 0, 0))
    draw.text((320 * scale, 276 * scale), addr_l1, font=font_reg, fill=(0, 0, 0))
    draw.text((320 * scale, 292 * scale), addr_l2, font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 325 * scale), (width - (30 * scale), 325 * scale)], fill=(0, 0, 0), width=2*scale)
    
    # 4. Item Table Grid Header (Matching Sample PDF Columns)
    draw.text((40 * scale, 335 * scale), "Description Of Goods", font=font_bold, fill=(0, 0, 0))
    draw.text((230 * scale, 335 * scale), "HSN", font=font_bold, fill=(0, 0, 0))
    draw.text((290 * scale, 335 * scale), "UNIT PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((370 * scale, 335 * scale), "QTY", font=font_bold, fill=(0, 0, 0))
    draw.text((410 * scale, 335 * scale), "GROSS PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((500 * scale, 335 * scale), "DISCOUNT", font=font_bold, fill=(0, 0, 0))
    draw.text((580 * scale, 335 * scale), "IGST", font=font_bold, fill=(0, 0, 0))
    draw.text((660 * scale, 335 * scale), "TOTAL VALUE", font=font_bold, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 355 * scale), (width - (30 * scale), 355 * scale)], fill=(0, 0, 0), width=2*scale)
    
    item = random.choice(LK_ITEMS_CATALOG)
    qty = 1
    unit_price = item[2]
    discount = item[3]
    gross_price = unit_price * qty
    taxable_val = round(gross_price - discount, 2)
    igst_rate = 0.18
    igst_val = round(taxable_val * igst_rate, 2)
    total_val = round(taxable_val + igst_val, 2)
    
    # Item Row
    draw.text((40 * scale, 365 * scale), item[0], font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 380 * scale), item[1], font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 395 * scale), f"-Product Id: {random.randint(100000, 999999)}, Inclusive of Premium Anti-Glare Lenses", font=font_reg, fill=(0, 0, 0))
    
    draw.text((230 * scale, 365 * scale), "90049020", font=font_reg, fill=(0, 0, 0))
    draw.text((290 * scale, 365 * scale), f"{unit_price:.2f}", font=font_reg, fill=(0, 0, 0))
    draw.text((370 * scale, 365 * scale), f"{qty} PCs", font=font_reg, fill=(0, 0, 0))
    draw.text((410 * scale, 365 * scale), f"{gross_price:.2f}", font=font_reg, fill=(0, 0, 0))
    draw.text((500 * scale, 365 * scale), f"{discount:.2f}", font=font_reg, fill=(0, 0, 0))
    draw.text((580 * scale, 365 * scale), f"18.0%", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 365 * scale), f"{total_val:.2f} INR", font=font_bold, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 480 * scale), (width - (30 * scale), 480 * scale)], fill=(0, 0, 0), width=2*scale)
    
    # 5. Bottom Grid: Scannable QR Code + Totals + Disclaimers + Paste Real Signature
    draw_qr_code(canvas, 140 * scale, 500 * scale, size=85 * scale, data_str=f"https://www.lenskart.com/taxinvoice/verify/{order_id}")
    
    draw.text((360 * scale, 495 * scale), "Total Taxable Amount :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 495 * scale), f"{taxable_val:.2f} INR", font=font_reg, fill=(0, 0, 0))
    draw.text((360 * scale, 515 * scale), "IGST (18%) :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 515 * scale), f"{igst_val:.2f} INR", font=font_reg, fill=(0, 0, 0))
    draw.text((360 * scale, 535 * scale), "CGST / SGST :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 535 * scale), "0.00 INR", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(350 * scale, 555 * scale), (width - (30 * scale), 555 * scale)], fill=(0, 0, 0), width=2*scale)
    draw.text((360 * scale, 565 * scale), "Grand Total (incl. of taxes) :", font=font_bold, fill=(0, 0, 0))
    draw.text((660 * scale, 565 * scale), f"{total_val:.2f} INR", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40 * scale, 600 * scale), f"Total Price: INR {total_val:.2f} rupees only", font=font_bold, fill=(0, 0, 0))
    
    # Disclaimers
    draw.text((40 * scale, 640 * scale), "Disclaimer:", font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 655 * scale), "1. This is computer generated invoice", font=font_small, fill=(50, 50, 50))
    draw.text((40 * scale, 668 * scale), "2. For other T&C Please refer our website www.lenskart.com", font=font_small, fill=(50, 50, 50))
    draw.text((40 * scale, 681 * scale), "3. Tax is payable on reverse charge basis: No", font=font_small, fill=(50, 50, 50))
    draw.text((40 * scale, 694 * scale), "4. The information provided in the invoice is true and correct", font=font_small, fill=(50, 50, 50))
    
    # Paste Real Signature Image
    sig_img = get_asset_image("lk_signature_real.png")
    if sig_img:
        sw, sh = sig_img.size
        tw = int(220 * scale)
        th = int(sh * (tw / sw))
        sig_resized = sig_img.resize((tw, th), Image.Resampling.LANCZOS)
        canvas.paste(sig_resized, (560 * scale, 620 * scale), sig_resized)
    else:
        draw.text((540 * scale, 630 * scale), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
        
    draw.text((550 * scale, 690 * scale), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
    data_summary = {
        "store_name": "LENSKART SOLUTIONS LIMITED",
        "store_addr": f"Delivered to {cust[0]} ({cust[1][:25]})",
        "total": total_val
    }
    return canvas, data_summary

# ─── Main Generation API ───

def generate_receipt_image(*args, **kwargs):
    """
    Main API to generate a restaurant/retail bill image matching the reference image.
    Outputs the receipt in full edge-to-edge 3:4 aspect ratio with the striped texture.
    """
    text_color = (15, 15, 15)   # Charcoal print ink
    
    # 1. Generate receipt data
    data = get_receipt_data()
    
    # 2. Render text directly on the striped canvas and return
    return draw_receipt_canvas(data, text_color), data
