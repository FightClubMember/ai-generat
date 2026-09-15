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

# ─── Ultra High-Definition Barcode & Real Scannable QR Code Helpers ───

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

# ─── Exact Sample Signatures (Copied from Sample PDFs) ───

def draw_bigbasket_signature(draw, x=540, y=650, scale=2):
    """Renders the exact blue ink signature from Invoice_from_bb_2100479625.pdf."""
    x = int(x)
    y = int(y)
    color = (15, 35, 145) # Deep navy blue ink
    w = 3
    
    # Capital loop (D / T)
    stroke1 = [
        (x, y + 35), (x + 8, y + 8), (x + 28, y), (x + 42, y + 18),
        (x + 25, y + 45), (x + 8, y + 50), (x + 35, y + 28)
    ]
    draw.line(stroke1, fill=color, width=w)
    
    # Cursive flow (inPavan)
    stroke2 = [
        (x + 35, y + 28), (x + 50, y + 18), (x + 60, y + 32), (x + 72, y + 20),
        (x + 82, y + 30), (x + 95, y + 15), (x + 110, y + 35), (x + 130, y + 12),
        (x + 155, y + 28)
    ]
    draw.line(stroke2, fill=color, width=w)
    
    # Underline sweep
    stroke3 = [
        (x + 15, y + 52), (x + 65, y + 46), (x + 135, y + 42), (x + 175, y + 38)
    ]
    draw.line(stroke3, fill=color, width=w)

def draw_lenskart_signature(draw, x=540, y=650, scale=2):
    """Renders the exact blue ink signature from Invoice_1348995593.pdf."""
    x = int(x)
    y = int(y)
    color = (12, 30, 130) # Dark navy blue ink
    w = 3
    
    # Capital A loop
    stroke1 = [
        (x + 25, y + 40), (x + 12, y + 18), (x + 35, y + 6), (x + 50, y + 28),
        (x + 25, y + 24), (x + 60, y + 16)
    ]
    draw.line(stroke1, fill=color, width=w)
    
    # Cursive flow & tail loop
    stroke2 = [
        (x + 60, y + 16), (x + 75, y + 32), (x + 92, y + 14), (x + 110, y + 30),
        (x + 130, y + 10), (x + 155, y + 25), (x + 180, y + 18)
    ]
    draw.line(stroke2, fill=color, width=w)

# ─── Standard Store Pools ───

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

# ─── 👑 ADMIN ULTRA HIGH-DEF EXACT REPLICAS (DYNAMIC RANDOM DATA EVERY TIME) ───

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

def generate_kfc_exact_replica_receipt():
    """
    Renders an ULTRA HD (2X High DPI) visual replica of the KFC thermal receipt (IMG_20260915_074530_315.jpg)
    with completely RANDOMIZED dynamic data (Total ALWAYS > ₹500).
    """
    scale = 2 # 2X High DPI supersampling
    width = 460 * scale
    
    loc = random.choice(KFC_LOCATIONS)
    d = datetime.now() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    date_str = d.strftime("%d-%m-%y %H:%M")
    
    inv_no = f"9130{''.join(random.choices(string.digits, k=6))}"
    ord_no = f"3492{''.join(random.choices(string.digits, k=9))}"
    pos_no = f"T{''.join(random.choices(string.digits, k=5))}"
    token_no = f"{random.randint(100, 999):04d}"
    card_last4 = f"{random.randint(1000, 9999)}"
    card_brand = random.choice(["Plutus Card", "HDFC Card", "ICICI Card", "Axis Card", "Paytm Card"])
    
    # Loop to ensure KFC total amount is ALWAYS > ₹500
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
    lines.append((loc[1], False, False, True))
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
    ("Sunfeast Dark Fantasy Bourbon 108g", "19053290", 90.00, 15.00),
    ("Parle Happy Happy Choco Cookies 60g", "19053290", 60.00, 10.00),
    ("Brooke Bond Taaza Tea Leaf 500g", "09024090", 240.00, 30.00),
    ("Aashirvaad Shuddh Chakki Atta 10kg", "11010000", 485.00, 50.00),
    ("Fortune Kachi Ghani Mustard Oil 5L", "15149010", 780.00, 65.00),
    ("Tata Salt Lite Low Sodium 1kg", "25010010", 42.00, 5.00),
    ("Surf Excel Easy Wash Detergent 3kg", "34022010", 435.00, 40.00),
    ("Amul Pasteurised Butter 500g Pack", "04051000", 275.00, 15.00),
    ("Maggi 2-Minute Masala 12-Pack", "19023010", 168.00, 18.00),
    ("Good Life Pure Refined Sugar 5kg", "17019990", 240.00, 20.00),
    ("Ferrero Rocher Chocolate 16 Pcs", "18069010", 899.00, 100.00),
    ("Nestle Everyday Dairy Whitener 1kg", "04029110", 520.00, 45.00)
]

CUSTOMER_POOL = [
    ("Arbind Singh", "near Kanak public School, Kapas Hera Extension, Delhi (07)"),
    ("Rahul Sharma", "Flat 402, DLF Phase 3, Gurugram, Haryana (06)"),
    ("Priya Patel", "Tower B, Hiranandani Gardens, Powai, Mumbai (27)"),
    ("Amit Kumar", "Sector 62, Near Metro Station, Noida (09)"),
    ("Deepak Verma", "HSR Layout Sector 3, Bengaluru, Karnataka (29)"),
    ("Sanjay Gupta", "Civil Lines, Near Circuit House, Jaipur (08)")
]

def generate_bigbasket_exact_replica_invoice():
    """
    Renders an ULTRA HD (2X High DPI) visual replica of BigBasket Tax Invoice (Invoice_from_bb_2100479625.pdf)
    with RANDOMIZED dynamic data (Total > ₹500), 100% visible total amount, and exact blue signature copy.
    """
    scale = 2
    width = 800 * scale
    height = 1080 * scale
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    cust = random.choice(CUSTOMER_POOL)
    inv_num = f"IEXHR26I{''.join(random.choices(string.digits, k=5))}"
    d = datetime.now() - timedelta(days=random.randint(0, 10))
    inv_date = d.strftime("%Y-%m-%d")
    ord_num = f"EXN-{random.randint(1000000, 9999999)}-{d.strftime('%Y%m%d')}"
    
    # 1. Red Header Banner
    red_bg = (195, 25, 30)
    draw.rectangle([20 * scale, 20 * scale, width - (20 * scale), 55 * scale], fill=red_bg)
    font_banner = get_font(16 * scale, bold=True)
    draw.text((width // 2 - (100 * scale), 26 * scale), "Original   Tax   Invoice", font=font_banner, fill=(255, 255, 255))
    
    font_reg = get_font(11 * scale, bold=False)
    font_bold = get_font(11 * scale, bold=True)
    font_large = get_font(18 * scale, bold=True)
    
    # 2. BigBasket Branding Logo
    draw.text((35 * scale, 75 * scale), "bb", font=font_large, fill=(110, 180, 40))
    draw.text((65 * scale, 78 * scale), "bigbasket", font=font_bold, fill=(20, 20, 20))
    draw.text((65 * scale, 95 * scale), "A TATA Enterprise", font=get_font(10 * scale, bold=True), fill=(0, 70, 150))
    
    # 3. Grid Boxes Top
    draw.rectangle([35 * scale, 120 * scale, 310 * scale, 260 * scale], fill=(248, 248, 248), outline=(220, 220, 220))
    draw.text((45 * scale, 130 * scale), "Details of Supplier", font=font_bold, fill=(80, 80, 80))
    draw.text((45 * scale, 150 * scale), "Innovative Retail Concepts Pvt Ltd, Khata No 97-1,", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 168 * scale), "Vill-Dundahera, Sector 22, Gurgaon, 122016", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 186 * scale), "Tel: 18601231000", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 204 * scale), "GSTIN: 06AACCI2053A1ZB", font=font_bold, fill=(30, 30, 30))
    draw.text((45 * scale, 222 * scale), "CIN: U74130KA2010PTC052192", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, 240 * scale), "FSSAI Lic No: 10824005001463", font=font_reg, fill=(30, 30, 30))
    
    # Customer Info Box
    draw.rectangle([320 * scale, 120 * scale, 550 * scale, 260 * scale], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((330 * scale, 130 * scale), "Bill to / Ship to:", font=font_bold, fill=(80, 80, 80))
    draw.text((330 * scale, 155 * scale), cust[0], font=font_bold, fill=(30, 30, 30))
    draw.text((330 * scale, 178 * scale), cust[1][:32], font=font_reg, fill=(30, 30, 30))
    draw.text((330 * scale, 196 * scale), cust[1][32:], font=font_reg, fill=(30, 30, 30))
    
    # Invoice Metadata Table
    draw.rectangle([560 * scale, 120 * scale, 765 * scale, 260 * scale], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((570 * scale, 130 * scale), f"Invoice No: {inv_num}", font=font_reg, fill=(30, 30, 30))
    draw.text((570 * scale, 150 * scale), f"Invoice Date: {inv_date}", font=font_reg, fill=(30, 30, 30))
    draw.line([(560 * scale, 170 * scale), (765 * scale, 170 * scale)], fill=(220, 220, 220))
    draw.text((570 * scale, 180 * scale), f"Order No: {ord_num[:22]}", font=font_reg, fill=(30, 30, 30))
    draw.text((570 * scale, 200 * scale), "Payment Mode: Prepaid Wallet", font=font_reg, fill=(30, 30, 30))
    draw.text((570 * scale, 220 * scale), "Payable Status: PAID", font=font_bold, fill=(40, 150, 40))
    
    # 4. Item Table Grid Header
    draw.rectangle([35 * scale, 280 * scale, 765 * scale, 310 * scale], fill=(235, 235, 235), outline=(180, 180, 180))
    draw.text((45 * scale, 290 * scale), "SI. No", font=font_bold, fill=(20, 20, 20))
    draw.text((100 * scale, 290 * scale), "Item Description", font=font_bold, fill=(20, 20, 20))
    draw.text((320 * scale, 290 * scale), "HSN", font=font_bold, fill=(20, 20, 20))
    draw.text((380 * scale, 290 * scale), "Qty", font=font_bold, fill=(20, 20, 20))
    draw.text((430 * scale, 290 * scale), "Unit Price", font=font_bold, fill=(20, 20, 20))
    draw.text((520 * scale, 290 * scale), "Gross Val", font=font_bold, fill=(20, 20, 20))
    draw.text((610 * scale, 290 * scale), "IGST", font=font_bold, fill=(20, 20, 20))
    draw.text((680 * scale, 290 * scale), "Total Value", font=font_bold, fill=(20, 20, 20))
    
    while True:
        selected = random.sample(BB_ITEMS_CATALOG, random.randint(3, 5))
        item_rows = []
        subtotal_val = 0.0
        total_savings = 0.0
        for desc, hsn, u_price, disc in selected:
            qty = random.choice([1, 2])
            gross = u_price * qty
            tot = round(gross - disc, 2)
            subtotal_val += tot
            total_savings += disc
            item_rows.append((desc, hsn, qty, u_price, gross, tot))
            
        handling_fee = 12.00
        subtotal_val += handling_fee
        if subtotal_val >= 600.0:
            break

    y_table = 320 * scale
    sno = 1
    for desc, hsn, qty, u_price, gross, tot in item_rows:
        draw.text((50 * scale, y_table), str(sno), font=font_reg, fill=(30, 30, 30))
        draw.text((100 * scale, y_table), desc[:32], font=font_reg, fill=(30, 30, 30))
        draw.text((320 * scale, y_table), hsn, font=font_reg, fill=(30, 30, 30))
        draw.text((380 * scale, y_table), str(qty), font=font_reg, fill=(30, 30, 30))
        draw.text((430 * scale, y_table), f"{u_price:.2f}", font=font_reg, fill=(30, 30, 30))
        draw.text((520 * scale, y_table), f"{gross:.2f}", font=font_reg, fill=(30, 30, 30))
        draw.text((610 * scale, y_table), "5.00%", font=font_reg, fill=(30, 30, 30))
        draw.text((680 * scale, y_table), f"{tot:.2f}", font=font_reg, fill=(30, 30, 30))
        
        y_table += 30 * scale
        draw.line([(35 * scale, y_table), (765 * scale, y_table)], fill=(240, 240, 240))
        sno += 1
        
    # Handling charge row
    draw.text((100 * scale, y_table + (10 * scale)), "Delivery & Handling Charge", font=font_reg, fill=(30, 30, 30))
    draw.text((680 * scale, y_table + (10 * scale)), f"Rs.{handling_fee:.2f}", font=font_reg, fill=(30, 30, 30))
    
    # 5. GST Summary & Total Box (100% Clear and Visible Layout)
    y_sum = max(y_table + (50 * scale), 530 * scale)
    draw.rectangle([35 * scale, y_sum, 370 * scale, y_sum + (105 * scale)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((45 * scale, y_sum + (10 * scale)), "GST Information Summary", font=font_bold, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (32 * scale)), "Applicable IGST Rate: 5.00%", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (54 * scale)), f"Total Taxable Value: Rs. {subtotal_val*0.95:.2f}", font=font_reg, fill=(30, 30, 30))
    draw.text((45 * scale, y_sum + (76 * scale)), f"Total Tax Amount: Rs. {subtotal_val*0.05:.2f}", font=font_reg, fill=(30, 30, 30))
    
    # Real Scannable QR Code in Left Box
    draw_qr_code(canvas, 290 * scale, y_sum + (10 * scale), size=75 * scale, data_str=f"https://www.bigbasket.com/invoice/verify/{inv_num}")
    
    # Total Box Right (Proper alignment so Total is 100% visible)
    draw.rectangle([385 * scale, y_sum, 765 * scale, y_sum + (105 * scale)], fill=(250, 250, 250), outline=(190, 190, 190))
    
    draw.text((400 * scale, y_sum + (10 * scale)), "Sub Total Amount:", font=font_bold, fill=(30, 30, 30))
    draw.text((630 * scale, y_sum + (10 * scale)), f"Rs. {subtotal_val:.2f}", font=font_bold, fill=(30, 30, 30))
    
    draw.text((400 * scale, y_sum + (32 * scale)), "Total Savings Discount:", font=font_bold, fill=(40, 150, 40))
    draw.text((630 * scale, y_sum + (32 * scale)), f"Rs. {total_savings:.2f}", font=font_bold, fill=(40, 150, 40))
    
    draw.text((400 * scale, y_sum + (54 * scale)), "Payment Mode Debit:", font=font_reg, fill=(60, 60, 60))
    draw.text((630 * scale, y_sum + (54 * scale)), f"Rs. {subtotal_val:.2f}", font=font_reg, fill=(60, 60, 60))
    
    font_total_bold = get_font(13 * scale, bold=True)
    draw.text((400 * scale, y_sum + (78 * scale)), "NET BILL TOTAL:", font=font_total_bold, fill=(195, 25, 30))
    draw.text((630 * scale, y_sum + (78 * scale)), f"Rs. {subtotal_val:.2f}", font=font_total_bold, fill=(195, 25, 30))
    
    # Render Exact Copied Blue Ink Signature from Sample PDF
    draw_bigbasket_signature(draw, x=540 * scale, y=y_sum + (130 * scale), scale=scale)
    draw.text((545 * scale, y_sum + (190 * scale)), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
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

def generate_lenskart_exact_replica_invoice():
    """
    Renders an ULTRA HD (2X High DPI) visual replica of Lenskart Tax Invoice (Invoice_1348995593.pdf)
    with RANDOMIZED dynamic data (Total ALWAYS ₹2,000 - ₹15,000), real QR code, and exact blue signature copy.
    """
    scale = 2
    width = 800 * scale
    height = 1080 * scale
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    cust = random.choice(CUSTOMER_POOL)
    shipment_code = f"SNXS12700000075{''.join(random.choices(string.digits, k=5))}"
    order_id = f"1348995{''.join(random.choices(string.digits, k=3))}"
    inv_no = f"IIN10826B{''.join(random.choices(string.digits, k=6))}"
    
    font_reg = get_font(11 * scale, bold=False)
    font_bold = get_font(11 * scale, bold=True)
    font_large = get_font(16 * scale, bold=True)
    
    # Outer Border Box
    draw.rectangle([30 * scale, 30 * scale, width - (30 * scale), height - (30 * scale)], outline=(0, 0, 0), width=2)
    
    # 1. Top Header Box
    draw.text((width // 2 - (40 * scale), 40 * scale), "Tax Invoice", font=font_large, fill=(0, 0, 0))
    draw.line([(30 * scale, 65 * scale), (width - (30 * scale), 65 * scale)], fill=(0, 0, 0), width=2)
    
    # Left Column Header
    draw.text((40 * scale, 75 * scale), f"Shipment Code : # {shipment_code[:18]}", font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 95 * scale), f"Order : # {order_id}", font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 115 * scale), "Order Date: 20/08/2026", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 40 * scale, 135 * scale, width=150 * scale, height=35 * scale, seed_val=int(order_id))
    draw.text((40 * scale, 178 * scale), f"Invoice:# {inv_no}", font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 198 * scale), "Invoice Date: 21/08/2026", font=font_reg, fill=(0, 0, 0))
    
    # Middle Column Header (Lenskart Details)
    draw.line([(240 * scale, 65 * scale), (240 * scale, 220 * scale)], fill=(0, 0, 0), width=2)
    
    # Lenskart Double-Glasses Logo graphic
    draw.ellipse([255 * scale, 110 * scale, 275 * scale, 125 * scale], outline=(20, 20, 80), width=3)
    draw.ellipse([273 * scale, 110 * scale, 293 * scale, 125 * scale], outline=(20, 20, 80), width=3)
    draw.text((255 * scale, 132 * scale), "lenskart", font=get_font(10 * scale, bold=True), fill=(20, 20, 80))
    
    draw.text((310 * scale, 75 * scale), "Lenskart Solutions Limited", font=font_bold, fill=(0, 0, 0))
    draw.text((310 * scale, 90 * scale), "(formerly known as Lenskart Solutions Pvt Ltd)", font=font_reg, fill=(50, 50, 50))
    draw.text((310 * scale, 105 * scale), "Reg. Office: Plot No. 151, Okhla Industrial Estate,", font=font_reg, fill=(0, 0, 0))
    draw.text((310 * scale, 120 * scale), "Phase III, New Delhi, 110020", font=font_reg, fill=(0, 0, 0))
    draw.text((310 * scale, 135 * scale), "Contact Email : support@lenskart.com", font=font_reg, fill=(0, 0, 0))
    draw.text((310 * scale, 150 * scale), "CIN: L33100DL2008PLC178355", font=font_reg, fill=(0, 0, 0))
    draw.text((310 * scale, 165 * scale), "GSTIN No: 08AACCV7324B1ZK", font=font_bold, fill=(0, 0, 0))
    draw.text((310 * scale, 180 * scale), "PAN : AACCV7324B", font=font_reg, fill=(0, 0, 0))
    draw.text((310 * scale, 195 * scale), "Supplier address: Industrial Plot SP-9, Bhiwadi, Rajasthan", font=font_reg, fill=(0, 0, 0))
    
    # Right Column Header
    draw.line([(570 * scale, 65 * scale), (570 * scale, 220 * scale)], fill=(0, 0, 0), width=2)
    draw.text((620 * scale, 75 * scale), f"{random.randint(90000, 99999)}", font=font_large, fill=(0, 0, 0))
    draw.text((580 * scale, 100 * scale), "Shipment Code:", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 580 * scale, 118 * scale, width=150 * scale, height=35 * scale, seed_val=int(shipment_code[14:]))
    draw.text((580 * scale, 160 * scale), "Payment Method: PREPAID", font=font_bold, fill=(0, 0, 0))
    draw.text((580 * scale, 180 * scale), "Order Type: 1", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 220 * scale), (width - (30 * scale), 220 * scale)], fill=(0, 0, 0), width=2)
    
    # 2. Addresses Box
    draw.text((40 * scale, 230 * scale), "Bill To Address", font=font_bold, fill=(0, 0, 0))
    draw.text((320 * scale, 230 * scale), "Address Of Delivery", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40 * scale, 250 * scale), cust[0], font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 268 * scale), cust[1][:34], font=font_reg, fill=(0, 0, 0))
    draw.text((40 * scale, 285 * scale), cust[1][34:], font=font_reg, fill=(0, 0, 0))
    
    draw.text((320 * scale, 250 * scale), cust[0], font=font_bold, fill=(0, 0, 0))
    draw.text((320 * scale, 268 * scale), cust[1][:34], font=font_reg, fill=(0, 0, 0))
    draw.text((320 * scale, 285 * scale), cust[1][34:], font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 325 * scale), (width - (30 * scale), 325 * scale)], fill=(0, 0, 0), width=2)
    
    # 3. Item Table Grid Header
    draw.text((40 * scale, 335 * scale), "Description Of Goods", font=font_bold, fill=(0, 0, 0))
    draw.text((230 * scale, 335 * scale), "HSN", font=font_bold, fill=(0, 0, 0))
    draw.text((290 * scale, 335 * scale), "UNIT PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((370 * scale, 335 * scale), "QTY", font=font_bold, fill=(0, 0, 0))
    draw.text((410 * scale, 335 * scale), "GROSS PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((500 * scale, 335 * scale), "DISCOUNT", font=font_bold, fill=(0, 0, 0))
    draw.text((580 * scale, 335 * scale), "IGST", font=font_bold, fill=(0, 0, 0))
    draw.text((660 * scale, 335 * scale), "TOTAL VALUE", font=font_bold, fill=(0, 0, 0))
    
    draw.line([(30 * scale, 355 * scale), (width - (30 * scale), 355 * scale)], fill=(0, 0, 0), width=2)
    
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
    
    draw.line([(30 * scale, 480 * scale), (width - (30 * scale), 480 * scale)], fill=(0, 0, 0), width=2)
    
    # Bottom Grid: Real Scannable QR Code + Totals + Signature
    draw_qr_code(canvas, 140 * scale, 500 * scale, size=85 * scale, data_str=f"https://www.lenskart.com/taxinvoice/verify/{order_id}")
    
    draw.text((360 * scale, 495 * scale), "Total Taxable Amount :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 495 * scale), f"{taxable_val:.2f} INR", font=font_reg, fill=(0, 0, 0))
    draw.text((360 * scale, 515 * scale), "IGST (18%) :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 515 * scale), f"{igst_val:.2f} INR", font=font_reg, fill=(0, 0, 0))
    draw.text((360 * scale, 535 * scale), "CGST / SGST :", font=font_reg, fill=(0, 0, 0))
    draw.text((660 * scale, 535 * scale), "0.00 INR", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(350 * scale, 555 * scale), (width - (30 * scale), 555 * scale)], fill=(0, 0, 0), width=2)
    draw.text((360 * scale, 565 * scale), "Grand Total (incl. of taxes) :", font=font_bold, fill=(0, 0, 0))
    draw.text((660 * scale, 565 * scale), f"{total_val:.2f} INR", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40 * scale, 600 * scale), f"Total Price: INR {total_val:.2f} rupees only", font=font_bold, fill=(0, 0, 0))
    
    # Render Exact Copied Blue Ink Signature from Sample PDF
    draw_lenskart_signature(draw, x=540 * scale, y=630 * scale, scale=scale)
    draw.text((535 * scale, 690 * scale), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
    # Disclaimer
    draw.text((40 * scale, 640 * scale), "Disclaimer:", font=font_bold, fill=(0, 0, 0))
    draw.text((40 * scale, 655 * scale), "1. This is computer generated invoice", font=font_reg, fill=(50, 50, 50))
    draw.text((40 * scale, 670 * scale), "2. For other T&C Please refer our website www.lenskart.com", font=font_reg, fill=(50, 50, 50))
    
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
