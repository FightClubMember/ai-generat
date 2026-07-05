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

# ─── Dynamic Restaurant Pools (Multiple Indian Cafes & Hotels) ───

STORE_FOOTER = "THANK YOU VISIT AGAIN !!!"

STORES_POOL = [
    {
        "name": "ROYAL CHINESE GARDEN",
        "subtitle": "(AUTHENTIC CHINESE CUISINE)",
        "address": "Unit 3, LBS Marg, Ghatkopar West",
        "city": "Mumbai, India",
        "tel": "022-25118877",
        "gstin": "27FFGGH7890P5Z2",
        "items": [
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
            ("Masala Papad", 60.00)
        ]
    },
    {
        "name": "SHREE DEVI VEG COURT",
        "subtitle": "(PURE VEG SOUTH INDIAN)",
        "address": "Shop 12, MG Road, Fort",
        "city": "Mumbai, India",
        "tel": "022-22669911",
        "gstin": "27AAACS1234D1Z5",
        "items": [
            ("Masala Dosa", 120.00),
            ("Idli Sambhar", 80.00),
            ("Medu Vada", 90.00),
            ("Filter Coffee", 50.00),
            ("Onion Uttapam", 110.00),
            ("Rava Dosa", 130.00),
            ("Butter Dosa", 140.00),
            ("Veg Pulao", 180.00),
            ("Sweet Lassi", 90.00),
            ("Thums Up", 40.00)
        ]
    },
    {
        "name": "THE TAJ PALACE HOTEL",
        "subtitle": "(MUGHLAI FINE DINING)",
        "address": "Apollo Bunder, Colaba",
        "city": "Mumbai, India",
        "tel": "022-66653366",
        "gstin": "27TAJPH6789K2Z0",
        "items": [
            ("Butter Chicken", 480.00),
            ("Chicken Biryani", 420.00),
            ("Paneer Tikka", 360.00),
            ("Tandoori Roti", 40.00),
            ("Butter Naan", 70.00),
            ("Dal Tadka", 280.00),
            ("Veg Kadhai", 320.00),
            ("Garlic Kebab", 390.00),
            ("Jeera Rice", 180.00),
            ("Gulab Jamun", 120.00)
        ]
    },
    {
        "name": "CAFE COFFEE TIME",
        "subtitle": "(DELICIOUS SNACKS & BREWS)",
        "address": "Carter Road, Bandra West",
        "city": "Mumbai, India",
        "tel": "022-26448833",
        "gstin": "27CCFTM4567A1Z3",
        "items": [
            ("Cappuccino", 160.00),
            ("Cafe Latte", 170.00),
            ("Cold Coffee", 190.00),
            ("Cheese Sandwich", 150.00),
            ("Garlic Bread", 120.00),
            ("Chocolate Brownie", 140.00),
            ("French Fries", 110.00),
            ("Veg Burger", 130.00),
            ("Green Tea", 90.00),
            ("Vanilla Shake", 160.00)
        ]
    },
    {
        "name": "UDUPI REFRESHMENTS",
        "subtitle": "(FAST FOOD & VEG SNACKS)",
        "address": "Dadar West Station Road",
        "city": "Mumbai, India",
        "tel": "022-24335566",
        "gstin": "27UDUPI9876P2Z9",
        "items": [
            ("Mysore Masala Dosa", 130.00),
            ("Sada Dosa", 90.00),
            ("Paper Dosa", 150.00),
            ("Wada Pav (Plate)", 60.00),
            ("Special Tea", 30.00),
            ("Poori Bhaji", 100.00),
            ("Pav Bhaji", 140.00),
            ("Cheese Pav Bhaji", 170.00),
            ("Upma", 70.00),
            ("Sheera", 70.00)
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
    count = random.randint(3, 7)
    selected = random.sample(store["items"], count)
    
    for name, u_price in selected:
        qty = random.choices([1, 2], weights=[80, 20])[0]
        price = round(u_price, 2)
        items.append((name, qty, price))
        
    subtotal = round(sum(q * p for _, q, p in items), 2)
    tax_rate = 0.05  # 5% total tax (2.5% CGST + 2.5% SGST)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    table_no = f"T{random.randint(1, 30):02d}"
    servers = ["Kiran", "Rahul", "Amit", "Pooja", "Sanjay", "Deepak", "Rohan"]
    server_name = random.choice(servers)
    
    return {
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
        "footer_msg": STORE_FOOTER
    }

# ─── Striped Tabletop Background ───

def generate_striped_background(width, height):
    """Generates the vertical striped beige background from the reference photo."""
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

# ─── Core Receipt Canvas Generator ───

def draw_receipt_canvas(data, text_color):
    """Renders the receipt directly onto a 3:4 aspect ratio striped canvas."""
    lines = [] # Array of tuples: (text_line, is_bold, is_large)
    
    # Local helper functions for exact character grid formatting (42 characters wide)
    def center_line(text):
        if len(text) >= 42:
            return text[:42]
        spaces = (42 - len(text)) // 2
        return " " * spaces + text
        
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
    
    # ─── 1. Header Section (Center-aligned) ───
    lines.append((center_line(store_name.upper()), True, True))   # Large Bold Store Name
    lines.append((center_line(subtitle.upper()), True, False))   # Bold Subtitle
    # Address lines exactly formatted on 2 lines
    lines.append((center_line(data["address_line1"]), False, False))
    lines.append((center_line(data["address_line2"]), False, False))
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
        
    # Enforce 3:4 Aspect Ratio (width = height * 3 / 4)
    width = total_height * 3 // 4
    
    # Create the canvas using the striped background directly
    canvas = generate_striped_background(width, total_height)
    draw = ImageDraw.Draw(canvas)
    
    # Center the receipt text block horizontally (Roboto Mono 13 size text block is ~336px wide)
    x_offset = max(10, (width - 336) // 2)
    
    y = padding
    for line_text, is_bold, is_large in lines:
        if is_large:
            font = font_large_bold
            curr_line_h = 23
        else:
            font = font_bold if is_bold else font_reg
            curr_line_h = line_h
            
        draw.text((x_offset, y), line_text, font=font, fill=text_color)
        y += curr_line_h
        
    return canvas

# ─── Main Generation API ───

def generate_receipt_image(*args, **kwargs):
    """
    Main API to generate a restaurant bill image matching the reference image.
    Outputs the receipt in full edge-to-edge 3:4 aspect ratio with the striped texture.
    """
    text_color = (15, 15, 15)   # Charcoal print ink
    
    # 1. Generate receipt data
    data = get_receipt_data()
    
    # 2. Render text directly on the striped canvas and return
    return draw_receipt_canvas(data, text_color), data
