import os
import io
import json
import time
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

# ─── Barcode & QR Code Drawing Helpers ───

def draw_barcode(draw, x, y, width=140, height=30):
    """Renders clean vertical barcode lines."""
    random.seed(int(x + y))
    curr_x = x
    while curr_x < x + width:
        w = random.choice([1, 2, 3])
        draw.rectangle([curr_x, y, curr_x + w, y + height], fill=(20, 20, 20))
        curr_x += w + random.choice([1, 2, 3])

def draw_qr_code(draw, x, y, size=75):
    """Renders authentic 2D square QR code with position detection patterns."""
    draw.rectangle([x, y, x + size, y + size], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    # Top-left finder
    draw.rectangle([x + 4, y + 4, x + 24, y + 24], fill=(0, 0, 0))
    draw.rectangle([x + 8, y + 8, x + 20, y + 20], fill=(255, 255, 255))
    draw.rectangle([x + 10, y + 10, x + 18, y + 18], fill=(0, 0, 0))
    # Top-right finder
    draw.rectangle([x + size - 24, y + 4, x + size - 4, y + 24], fill=(0, 0, 0))
    draw.rectangle([x + size - 20, y + 8, x + size - 8, y + 20], fill=(255, 255, 255))
    draw.rectangle([x + size - 18, y + 10, x + size - 10, y + 18], fill=(0, 0, 0))
    # Bottom-left finder
    draw.rectangle([x + 4, y + size - 24, x + 24, y + size - 4], fill=(0, 0, 0))
    draw.rectangle([x + 8, y + size - 20, x + 20, y + size - 8], fill=(255, 255, 255))
    draw.rectangle([x + 10, y + size - 18, x + 18, y + size - 10], fill=(0, 0, 0))
    
    # Fill inner grid with data noise blocks
    random.seed(int(x * y))
    for rx in range(x + 28, x + size - 4, 4):
        for ry in range(y + 4, y + size - 4, 4):
            if random.random() > 0.4:
                draw.rectangle([rx, ry, rx + 3, ry + 3], fill=(0, 0, 0))

def draw_signature(draw, x, y):
    """Renders authentic blue ink cursive signature stroke."""
    points = [
        (x, y + 15), (x + 12, y + 5), (x + 22, y + 24), (x + 38, y + 8),
        (x + 50, y + 18), (x + 65, y + 2), (x + 80, y + 22), (x + 95, y + 12),
        (x + 115, y + 15)
    ]
    draw.line(points, fill=(15, 35, 140), width=2)

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
    },
    {
        "name": "LENSKART SOLUTIONS LTD",
        "subtitle": "(EYEWEAR OPTICAL RETAIL)",
        "address": "Plot 151, Okhla Ind. Estate, Phase III",
        "city": "New Delhi, 110020",
        "tel": "CIN: L33100DL2008PLC178355",
        "gstin": "08AACCV7324B1ZK",
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.12,
        "footer": "LOG ON TO LENSKART.COM FOR MORE",
        "layout_type": "grid",
        "items": [
            ("Lenskart Air Comfort Frame", 1694.92),
            ("BLU Screen Anti-Glare Lens", 1200.00),
            ("Vincent Chase Air Flex", 1500.00),
            ("Lens Cleaning Spray 100ml", 150.00)
        ]
    },
    {
        "name": "BLINKIT (GROFERS INDIA)",
        "subtitle": "(10-MINUTE QUICK COMMERCE)",
        "address": "Dark Store Hub #402, DLF Phase 3",
        "city": "Gurugram, Haryana, India",
        "tel": "0124-4556677",
        "gstin": "06AAACG9988F1Z1",
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "BLINKIT - DELIVERED IN 10 MINS!",
        "layout_type": "grid",
        "items": [
            ("Amul Butter 500g", 275.00),
            ("Amul Taaza Milk 1L", 74.00),
            ("Harvest Bread 400g", 50.00),
            ("Maggi Noodle 4-Pk", 56.00)
        ]
    },
    {
        "name": "ZEPTO QUICK COMMERCE",
        "subtitle": "(10-MIN EXPRESS GROCERY)",
        "address": "FC 12, HSR Layout, Sector 3",
        "city": "Bengaluru, Karnataka, India",
        "tel": "080-45689900",
        "gstin": "29AAACK7711Q1Z4",
        "separator": ".",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "ZEPTO - DELIVERED IN 10 MINS!",
        "layout_type": "lines",
        "items": [
            ("Epigamia Mango Yogurt", 60.00),
            ("Coca Cola Zero Can", 40.00),
            ("Lay's Magic Masala", 20.00),
            ("Red Bull Energy Drink", 125.00)
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

# ─── 👑 ADMIN PREMIUM REPLICAS ENGINE (Exact Replica Sample Images) ───

def generate_kfc_exact_replica_receipt():
    """
    Renders an EXACT visual replica of the KFC thermal receipt matching IMG_20260915_074530_315.jpg:
    - Red KFC vertical repeating border logos on both sides.
    - Large Token No and *DINE-IN* header.
    - Plutus Card payments breakdown.
    - Square QR Code at the bottom.
    """
    width = 460
    
    date_str = datetime.now().strftime("%d-%m-%y %H:%M")
    inv_no = f"9130{''.join(random.choices(string.digits, k=6))}"
    ord_no = f"3492{''.join(random.choices(string.digits, k=9))}"
    token_no = f"{random.randint(100, 999):04d}"
    card_last4 = f"{random.randint(1000, 9999)}"
    
    items = [
        ("Indian Spicy Veg Rol", 21350.00, 1, 0.00, 21350.00, []),
        ("ADDON REG FRIES & PEPSI", 14500.00, 1, None, 14500.00, ["  FRIES-REGULAR       1", "  PEPSI -REG          1"]),
        ("Chana Burger DI/TA", 6850.00, 1, 0.00, 6850.00, [])
    ]
    
    subtotal = sum(x[4] for x in items)
    sgst = subtotal * 0.025
    cgst = subtotal * 0.025
    total = subtotal + sgst + cgst
    
    lines = []
    lines.append(("KFC,", True, True, True))
    lines.append(("Devyani International Ltd.", True, False, True))
    lines.append(("Medanta - The Medicity", False, False, True))
    lines.append(("Sec-38, Gurgaon(Haryana)", False, False, True))
    lines.append(("POS: Haryana", False, False, True))
    lines.append(("GSTIN No.: 06AABCD5534A1Z9", False, False, True))
    lines.append(("Service Code Tariff: 996331", False, False, True))
    lines.append(("FSSAI No.: 10617005000139", False, False, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append(("INVOICE", True, False, True))
    lines.append((f"Inv No {inv_no}  ORD No  {ord_no[:10]}", False, False, False))
    lines.append((f"Date:  {date_str}  POS No.     T34913", False, False, False))
    lines.append((f"Token No:- {token_no}", True, True, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append(("*DINE-IN*", True, True, True))
    lines.append(("---------------------------------------", False, False, True))
    lines.append((f"{'Description':<14} {'Price':>8} {'Qty':>3} {'Disc.':>5} {'Amount':>8}", True, False, False))
    lines.append(("---------------------------------------", False, False, True))
    
    for name, price, qty, disc, amt, subs in items:
        lines.append((name, False, False, False))
        disc_str = f"{disc:.2f}" if disc is not None else ""
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
    lines.append((f"{'Plutus Card':<26} {total:>10.2f}", False, False, False))
    lines.append((f" {card_last4}", False, False, False))
    lines.append(("---------------------------------------", False, False, True))
    lines.append((f"{'Payments:':<26} {total:>10.2f}", False, False, False))
    lines.append(("---------------------------------------", False, False, True))
    
    font_reg = get_font(13, bold=False)
    font_bold = get_font(13, bold=True)
    font_large_bold = get_font(16, bold=True)
    font_kfc = get_font(14, bold=True)
    
    line_h = 19
    padding = 30
    total_height = padding * 2 + 100 # Extra space for bottom QR code
    
    for _, _, is_large, _ in lines:
        total_height += 23 if is_large else line_h
        
    canvas = Image.new("RGB", (width, total_height), (245, 245, 242))
    draw = ImageDraw.Draw(canvas)
    
    # ─── Draw Vertical Red KFC Side Border Logos ───
    red_color = (195, 16, 40) # Official KFC Red
    for y_pos in range(30, total_height - 60, 110):
        draw.text((12, y_pos), "KFC", font=font_kfc, fill=red_color)
        draw.text((width - 45, y_pos), "KFC", font=font_kfc, fill=red_color)
        
    y = padding
    text_color = (20, 20, 20)
    x_left = 60
    
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
            draw.text((x_left, y), line_text, font=font, fill=text_color)
            
        y += curr_line_h
        
    # Draw bottom square QR code
    draw_qr_code(draw, (width - 85) // 2, y + 10, size=85)
    
    data_summary = {
        "store_name": "KFC (Devyani International Ltd)",
        "store_addr": "Medanta - The Medicity, Sec-38, Gurgaon, Haryana",
        "total": total
    }
    return canvas, data_summary

def generate_bigbasket_exact_replica_invoice():
    """
    Renders an EXACT visual replica of the BigBasket Tax Invoice matching Invoice_from_bb_2100479625.pdf:
    - Red top banner: Original Tax Invoice.
    - BigBasket A TATA Enterprise logo.
    - Details of Supplier box, Bill to/Ship to box, Order Information table.
    - Full HSN item table grid.
    - Savings breakdown & Blue Ink Authorized Signatory signature.
    """
    width = 800
    height = 1050
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    # 1. Red Header Banner
    red_bg = (195, 25, 30)
    draw.rectangle([20, 20, width - 20, 55], fill=red_bg)
    font_banner = get_font(16, bold=True)
    draw.text((width // 2 - 80, 27), "Original   Tax   Invoice", font=font_banner, fill=(255, 255, 255))
    
    font_reg = get_font(12, bold=False)
    font_bold = get_font(12, bold=True)
    font_large = get_font(18, bold=True)
    
    # 2. BigBasket Branding Logo
    draw.text((35, 75), "bb", font=font_large, fill=(110, 180, 40))
    draw.text((60, 78), "bigbasket", font=font_bold, fill=(20, 20, 20))
    draw.text((60, 93), "A TATA Enterprise", font=get_font(10, bold=True), fill=(0, 70, 150))
    
    # 3. Grid Boxes Top
    draw.rectangle([35, 120, 310, 260], fill=(248, 248, 248), outline=(220, 220, 220))
    draw.text((45, 130), "Details of Supplier", font=font_bold, fill=(80, 80, 80))
    draw.text((45, 150), "Innovative Retail Concepts Pvt Ltd, Khata No 97-1,", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 165), "Vill-Dundahera, Sector 22, Gurgaon, 122016", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 185), "Tel: 18601231000", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 200), "GSTIN: 06AACCI2053A1ZB", font=font_bold, fill=(30, 30, 30))
    draw.text((45, 215), "CIN: U74130KA2010PTC052192", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 230), "FSSAI Lic No: 10824005001463", font=font_reg, fill=(30, 30, 30))
    
    # Customer Info Box
    draw.rectangle([320, 120, 550, 260], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((330, 130), "Bill to / Ship to:", font=font_bold, fill=(80, 80, 80))
    draw.text((330, 155), "Arbind Singh", font=font_bold, fill=(30, 30, 30))
    draw.text((330, 175), "near Kanak Public School", font=font_reg, fill=(30, 30, 30))
    draw.text((330, 190), "Kapas Hera Extension, Delhi", font=font_reg, fill=(30, 30, 30))
    draw.text((330, 205), "Delhi (07)", font=font_reg, fill=(30, 30, 30))
    
    # Invoice Metadata Table
    draw.rectangle([560, 120, 765, 260], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((570, 130), f"Invoice No: IEXHR26I{''.join(random.choices(string.digits, k=5))}", font=font_reg, fill=(30, 30, 30))
    draw.text((570, 150), f"Invoice Date: {datetime.now().strftime('%Y-%m-%d')}", font=font_reg, fill=(30, 30, 30))
    draw.line([(560, 170), (765, 170)], fill=(220, 220, 220))
    draw.text((570, 180), f"Order No: EXN-2100479-{random.randint(1000, 9999)}", font=font_reg, fill=(30, 30, 30))
    draw.text((570, 200), "Payment Mode: walletPrepaid", font=font_reg, fill=(30, 30, 30))
    draw.text((570, 220), "Payable Amount: Rs. 0.00", font=font_bold, fill=(30, 30, 30))
    
    # 4. Item Table Grid Header
    draw.rectangle([35, 280, 765, 310], fill=(235, 235, 235), outline=(180, 180, 180))
    draw.text((45, 290), "SI. No", font=font_bold, fill=(20, 20, 20))
    draw.text((100, 290), "Item Description", font=font_bold, fill=(20, 20, 20))
    draw.text((320, 290), "HSN", font=font_bold, fill=(20, 20, 20))
    draw.text((380, 290), "Qty", font=font_bold, fill=(20, 20, 20))
    draw.text((430, 290), "Unit Price", font=font_bold, fill=(20, 20, 20))
    draw.text((520, 290), "Gross Val", font=font_bold, fill=(20, 20, 20))
    draw.text((610, 290), "IGST", font=font_bold, fill=(20, 20, 20))
    draw.text((690, 290), "Total Value", font=font_bold, fill=(20, 20, 20))
    
    items = [
        ("1", "Sunfeast Dark Fantasy Bourbon 108g", "19053290", "1", "30.00", "30.83", "5.00%", "15.83"),
        ("2", "Parle Happy Happy Choco Cookies 60g", "19053290", "1", "10.00", "10.55", "5.00%", "10.55"),
        ("3", "Brooke Bond Taaza Tea Leaf 250g", "09024090", "2", "60.00", "126.62", "5.00%", "126.62")
    ]
    
    y_table = 320
    for sno, desc, hsn, qty, price, gross, igst, tot in items:
        draw.text((50, y_table), sno, font=font_reg, fill=(30, 30, 30))
        draw.text((100, y_table), desc[:30], font=font_reg, fill=(30, 30, 30))
        draw.text((320, y_table), hsn, font=font_reg, fill=(30, 30, 30))
        draw.text((380, y_table), qty, font=font_reg, fill=(30, 30, 30))
        draw.text((430, y_table), price, font=font_reg, fill=(30, 30, 30))
        draw.text((520, y_table), gross, font=font_reg, fill=(30, 30, 30))
        draw.text((610, y_table), igst, font=font_reg, fill=(30, 30, 30))
        draw.text((690, y_table), tot, font=font_reg, fill=(30, 30, 30))
        y_table += 30
        draw.line([(35, y_table), (765, y_table)], fill=(240, 240, 240))
        
    # Handling charge row
    draw.text((100, y_table + 10), "Handling Charge", font=font_reg, fill=(30, 30, 30))
    draw.text((690, y_table + 10), "Rs. 8.00", font=font_reg, fill=(30, 30, 30))
    
    # 5. GST Summary & Signature Box
    draw.rectangle([35, 500, 350, 590], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((45, 510), "GST Information", font=font_bold, fill=(30, 30, 30))
    draw.text((45, 530), "IGST Rate: 5.00%", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 550), "Taxable Value: Rs. 145.72", font=font_reg, fill=(30, 30, 30))
    draw.text((45, 570), "Tax Value: Rs. 7.28", font=font_reg, fill=(30, 30, 30))
    
    draw.rectangle([400, 500, 765, 590], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((410, 510), "Sub Total:", font=font_bold, fill=(30, 30, 30))
    draw.text((690, 510), "Rs. 153.00", font=font_bold, fill=(30, 30, 30))
    draw.text((410, 535), "Wallet Debit Availed:", font=font_reg, fill=(30, 30, 30))
    draw.text((690, 535), "Rs. 133.00", font=font_reg, fill=(30, 30, 30))
    draw.text((410, 560), "You Saved: Rs. 35.00", font=font_bold, fill=(40, 160, 40))
    draw.text((690, 560), "Final Total: Rs. 133.00", font=font_bold, fill=(30, 30, 30))
    
    # Blue Authorized Signatory signature
    draw_signature(draw, 550, 640)
    draw.text((545, 680), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
    data_summary = {
        "store_name": "BIGBASKET (Innovative Retail / A Tata Enterprise)",
        "store_addr": "Khata No 97-1, Vill-Dundahera, Sector 22, Gurgaon",
        "total": 133.00
    }
    return canvas, data_summary

def generate_lenskart_exact_replica_invoice():
    """
    Renders an EXACT visual replica of the Lenskart Tax Invoice matching Invoice_1348995593.pdf:
    - Lenskart double-glasses logo.
    - Top 3 Header Grid with Barcodes, Order No, Shipment Code, and Payment Method.
    - Bill To Address and Delivery Address Boxes.
    - Eyewear Goods Grid with HSN Code 90049020 and 18% IGST split.
    - Bottom QR Code, Total Price in Words, and Blue Ink Authorized Signatory signature.
    """
    width = 800
    height = 1050
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    font_reg = get_font(11, bold=False)
    font_bold = get_font(11, bold=True)
    font_large = get_font(16, bold=True)
    
    # Outer Border Box
    draw.rectangle([30, 30, width - 30, height - 30], outline=(0, 0, 0), width=1)
    
    # 1. Top Header Box
    draw.text((width // 2 - 40, 40), "Tax Invoice", font=font_large, fill=(0, 0, 0))
    draw.line([(30, 65), (width - 30, 65)], fill=(0, 0, 0), width=1)
    
    # Left Column Header
    shipment_code = f"SNXS12700000075{''.join(random.choices(string.digits, k=5))}"
    order_id = f"1348995{''.join(random.choices(string.digits, k=3))}"
    
    draw.text((40, 75), f"Shipment Code : # {shipment_code[:18]}", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 95), f"Order : # {order_id}", font=font_bold, fill=(0, 0, 0))
    draw.text((40, 115), "Order Date: 20/08/2026", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 40, 135, width=150, height=35)
    draw.text((40, 175), f"Invoice:# IIN10826B{''.join(random.choices(string.digits, k=6))}", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 195), "Invoice Date: 21/08/2026", font=font_reg, fill=(0, 0, 0))
    
    # Middle Column Header (Lenskart Details)
    draw.line([(240, 65), (240, 220)], fill=(0, 0, 0), width=1)
    
    # Lenskart Double-Glasses Logo graphic
    draw.ellipse([255, 110, 275, 125], outline=(20, 20, 80), width=2)
    draw.ellipse([273, 110, 293, 125], outline=(20, 20, 80), width=2)
    draw.text((255, 130), "lenskart", font=get_font(10, bold=True), fill=(20, 20, 80))
    
    draw.text((310, 75), "Lenskart Solutions Limited", font=font_bold, fill=(0, 0, 0))
    draw.text((310, 90), "(formerly known as Lenskart Solutions Pvt Ltd)", font=font_reg, fill=(50, 50, 50))
    draw.text((310, 105), "Reg. Office: Plot No. 151, Okhla Industrial Estate,", font=font_reg, fill=(0, 0, 0))
    draw.text((310, 120), "Phase III, New Delhi, 110020", font=font_reg, fill=(0, 0, 0))
    draw.text((310, 135), "Contact Email : support@lenskart.com", font=font_reg, fill=(0, 0, 0))
    draw.text((310, 150), "CIN: L33100DL2008PLC178355", font=font_reg, fill=(0, 0, 0))
    draw.text((310, 165), "GSTIN No: 08AACCV7324B1ZK", font=font_bold, fill=(0, 0, 0))
    draw.text((310, 180), "PAN : AACCV7324B", font=font_reg, fill=(0, 0, 0))
    draw.text((310, 195), "Supplier address: Industrial Plot SP-9, Bhiwadi, Rajasthan", font=font_reg, fill=(0, 0, 0))
    
    # Right Column Header
    draw.line([(570, 65), (570, 220)], fill=(0, 0, 0), width=1)
    draw.text((620, 75), "95593", font=font_large, fill=(0, 0, 0))
    draw.text((580, 100), "Shipment Code:", font=font_reg, fill=(0, 0, 0))
    draw_barcode(draw, 580, 118, width=150, height=35)
    draw.text((580, 160), "Payment Method: PREPAID", font=font_bold, fill=(0, 0, 0))
    draw.text((580, 180), "Order Type: 1", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30, 220), (width - 30, 220)], fill=(0, 0, 0), width=1)
    
    # 2. Addresses Box
    draw.text((40, 230), "Bill To Address", font=font_bold, fill=(0, 0, 0))
    draw.text((320, 230), "Address Of Delivery", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40, 250), "HIMANSHU kumar", font=font_bold, fill=(0, 0, 0))
    draw.text((40, 268), "01, jhikati urf salimpur hussain near Aman kirana store", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 285), "844127 Jhiki urf Salimpur Husain, Bihar 844127", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 302), "Place of supply: Bihar(10)", font=font_reg, fill=(0, 0, 0))
    
    draw.text((320, 250), "HIMANSHU kumar", font=font_bold, fill=(0, 0, 0))
    draw.text((320, 268), "01, jhikati urf salimpur hussain near Aman kirana store", font=font_reg, fill=(0, 0, 0))
    draw.text((320, 285), "844127 Jhiki urf Salimpur Husain, Bihar 844127", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(30, 325), (width - 30, 325)], fill=(0, 0, 0), width=1)
    
    # 3. Item Table Grid Header
    draw.text((40, 335), "Description Of Goods", font=font_bold, fill=(0, 0, 0))
    draw.text((230, 335), "HSN", font=font_bold, fill=(0, 0, 0))
    draw.text((290, 335), "UNIT PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((370, 335), "QTY", font=font_bold, fill=(0, 0, 0))
    draw.text((410, 335), "GROSS PRICE", font=font_bold, fill=(0, 0, 0))
    draw.text((500, 335), "DISCOUNT", font=font_bold, fill=(0, 0, 0))
    draw.text((580, 335), "IGST", font=font_bold, fill=(0, 0, 0))
    draw.text((660, 335), "TOTAL VALUE", font=font_bold, fill=(0, 0, 0))
    
    draw.line([(30, 355), (width - 30, 355)], fill=(0, 0, 0), width=1)
    
    # Item Row
    draw.text((40, 365), "Transparent Full Rim Square Lenskart Air", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 380), "Comfort LA E15019-C3 Eyeglasses", font=font_reg, fill=(0, 0, 0))
    draw.text((40, 395), "-Product Id: 204186, Inclusive of BLU Screen Lenses", font=font_reg, fill=(0, 0, 0))
    
    draw.text((230, 365), "90049020", font=font_reg, fill=(0, 0, 0))
    draw.text((290, 365), "1694.92", font=font_reg, fill=(0, 0, 0))
    draw.text((370, 365), "1 PCs", font=font_reg, fill=(0, 0, 0))
    draw.text((410, 365), "1694.92", font=font_reg, fill=(0, 0, 0))
    draw.text((500, 365), "1694.07", font=font_reg, fill=(0, 0, 0))
    draw.text((580, 365), "0.15 @18.0%", font=font_reg, fill=(0, 0, 0))
    draw.text((660, 365), "1.00 INR", font=font_bold, fill=(0, 0, 0))
    
    draw.line([(30, 480), (width - 30, 480)], fill=(0, 0, 0), width=1)
    
    # Bottom Grid: QR Code + Totals + Signature
    draw_qr_code(draw, 140, 500, size=75)
    
    draw.text((360, 495), "Total Taxable Amount :", font=font_reg, fill=(0, 0, 0))
    draw.text((660, 495), "0.85", font=font_reg, fill=(0, 0, 0))
    draw.text((360, 515), "IGST :", font=font_reg, fill=(0, 0, 0))
    draw.text((660, 515), "0.15", font=font_reg, fill=(0, 0, 0))
    draw.text((360, 535), "CGST / SGST :", font=font_reg, fill=(0, 0, 0))
    draw.text((660, 535), "0.00", font=font_reg, fill=(0, 0, 0))
    
    draw.line([(350, 555), (width - 30, 555)], fill=(0, 0, 0), width=1)
    draw.text((360, 565), "Grand Total (incl. of taxes) :", font=font_bold, fill=(0, 0, 0))
    draw.text((660, 565), "01.00 INR", font=font_bold, fill=(0, 0, 0))
    
    draw.text((40, 600), "Total Price in words : INR One rupees only", font=font_bold, fill=(0, 0, 0))
    
    # Signature box
    draw_signature(draw, 540, 640)
    draw.text((535, 680), "Authorized Signatory", font=font_bold, fill=(60, 60, 60))
    
    # Disclaimer
    draw.text((40, 640), "Disclaimer:", font=font_bold, fill=(0, 0, 0))
    draw.text((40, 655), "1. This is computer generated invoice", font=font_reg, fill=(50, 50, 50))
    draw.text((40, 670), "2. For other T&C Please refer our website www.lenskart.com", font=font_reg, fill=(50, 50, 50))
    
    data_summary = {
        "store_name": "LENSKART SOLUTIONS LIMITED",
        "store_addr": "Plot No. 151, Okhla Industrial Estate, Phase III, New Delhi",
        "total": 1.00
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
