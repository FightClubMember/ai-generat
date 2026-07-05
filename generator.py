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

# ─── Dynamic Restaurant Pools with Formats & Menus ───

STORES_POOL = [
    {
        "name": "ROYAL CHINESE GARDEN",
        "subtitle": "(AUTHENTIC CHINESE CUISINE)",
        "address": "Unit 3, LBS Marg, Ghatkopar West",
        "city": "Mumbai, India",
        "tel": "022-25118877",
        "gstin": "27FFGGH7890P5Z2",
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU VISIT AGAIN !!!",
        "layout_type": "grid",
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
        "separator": "=",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU VISIT AGAIN !!!",
        "layout_type": "grid",
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
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.18,  # Fine Dining 18% GST
        "footer": "THANK YOU FOR DINING WITH US",
        "layout_type": "grid",
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
        "separator": ".",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "HAVE A COFFEE-FILLED DAY!",
        "layout_type": "lines",
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
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU VISIT AGAIN !!!",
        "layout_type": "grid",
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
    },
    {
        "name": "PUNJABI DHABA & RESTAURANT",
        "subtitle": "(AUTHENTIC NORTH INDIAN)",
        "address": "NH-44 Highway, bypass road",
        "city": "Panipat, Haryana",
        "tel": "0180-2566778",
        "gstin": "",  # Local dhaba, no GSTIN
        "separator": "*",
        "has_gst": False,
        "tax_rate": 0.00,
        "footer": "APNA DHABA - GHAR JAISA SWAD !!!",
        "layout_type": "lines",
        "items": [
            ("Kadhai Paneer", 240.00),
            ("Shahi Paneer", 230.00),
            ("Dal Makhani", 190.00),
            ("Tandoori Butter Roti", 25.00),
            ("Butter Naan", 50.00),
            ("Jeera Aloo", 140.00),
            ("Sweet Lassi (Big)", 70.00),
            ("Mix Veg", 180.00),
            ("Boondi Raita", 90.00),
            ("Papad Roast", 30.00)
        ]
    },
    {
        "name": "JOHNY HOT DOG",
        "subtitle": "(INDORE'S MASHHOOR FAST FOOD)",
        "address": "Chappan Dukan, New Palasia",
        "city": "Indore, India",
        "tel": "0731-2522110",
        "gstin": "",
        "separator": "-",
        "has_gst": False,
        "tax_rate": 0.00,
        "footer": "JOHNY HOT DOG KA SWAD NO.1 !!!",
        "layout_type": "lines",
        "items": [
            ("Veg Banjo", 50.00),
            ("Egg Banjo", 60.00),
            ("Mutton Hotdog", 120.00),
            ("Cheese Veg Banjo", 70.00),
            ("Johny Special Bun", 40.00),
            ("French Fries", 80.00),
            ("Cold Coffee", 70.00),
            ("Cold Drink Pepsi", 40.00)
        ]
    },
    {
        "name": "BOMBAY SWEETS & BAKERY",
        "subtitle": "(SWEETS, NAMKEEN & BAKERY)",
        "address": "Opp. Railway Station, Dadar East",
        "city": "Mumbai, India",
        "tel": "022-24118833",
        "gstin": "27BOMSW9912A1Z4",
        "separator": "*",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "GOODS ONCE SOLD NOT RETURNED",
        "layout_type": "grid",
        "items": [
            ("Kaju Katli (250g)", 250.00),
            ("Motichoor Laddu (250g)", 150.00),
            ("Gulab Jamun (Plate)", 70.00),
            ("Rasgulla (Plate)", 70.00),
            ("Samosa Garam (Plate)", 40.00),
            ("Dhokla Fresh (250g)", 80.00),
            ("Special Jalebi (Plate)", 60.00),
            ("Aloo Tikki Chaat", 80.00),
            ("Dry Fruits Pack", 450.00)
        ]
    },
    {
        "name": "THE PIZZA CORNER",
        "subtitle": "(ITALIAN WOODFIRED PIZZAS)",
        "address": "G-10, Galleria Mall, Hiranandani",
        "city": "Powai, Mumbai",
        "tel": "022-25701100",
        "gstin": "27PZCNR7789M1Z8",
        "separator": "=",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU FOR FEASTING WITH US!",
        "layout_type": "grid",
        "items": [
            ("Margherita Pizza", 299.00),
            ("Paneer Tikka Pizza", 399.00),
            ("Veg Overloaded Pizza", 449.00),
            ("Garlic Bread Sticks", 139.00),
            ("Stuffed Garlic Bread", 199.00),
            ("Choco Lava Cake", 109.00),
            ("Veg White Pasta", 249.00),
            ("Pepsi Can", 60.00),
            ("Mineral Water Bottle", 40.00)
        ]
    },
    {
        "name": "SARAVANA BHAVAN",
        "subtitle": "(PREMIUM SOUTH INDIAN RESTAURANT)",
        "address": "Janpath, Connaught Place",
        "city": "New Delhi, India",
        "tel": "011-23311955",
        "gstin": "07SARAV9876Q1Z9",
        "separator": "-",
        "has_gst": True,
        "tax_rate": 0.05,
        "footer": "THANK YOU VISIT AGAIN !!!",
        "layout_type": "grid",
        "items": [
            ("Ghee Roast Dosa", 170.00),
            ("Special Idli Sambhar", 110.00),
            ("Medu Vada (2 Pcs)", 120.00),
            ("Saravana Spl Dosa", 210.00),
            ("Rava Masala Dosa", 190.00),
            ("South Indian Thali", 320.00),
            ("Mini Ghee Idlis (14)", 140.00),
            ("Madras Filter Coffee", 70.00),
            ("Fresh Mango Juice", 130.00)
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
        
    # Add very fine texture noise
    noise = Image.effect_noise((width, height), 6).convert("RGB")
    bg = Image.blend(bg, noise, 0.05)
    
    return bg

# ─── Core Receipt Canvas Generator ───

def draw_receipt_canvas(data, text_color):
    """Renders the receipt directly onto a 3:4 aspect ratio striped canvas with store-specific layouts."""
    lines = [] # Array of tuples: (text_line, is_bold, is_large, is_centered)
    
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
    
    # Store-specific separator
    sep_char = store.get("separator", "-")
    separator_line = sep_char * 42
    
    # ─── 1. Header Section ───
    lines.append((store_name.upper(), True, True, True))            # Large Bold Store Name (Centered)
    lines.append((subtitle.upper(), True, False, True))             # Bold Subtitle (Centered)
    lines.append((data["address_line1"], False, False, True))       # Address Line 1 (Centered)
    lines.append((data["address_line2"], False, False, True))       # Address Line 2 (Centered)
    lines.append((f"Tel: {tel_no}", False, False, True))            # Tel Line (Centered)
    
    # Include GSTIN only if it's set in store profile
    if gstin:
        lines.append((f"GSTIN: {gstin}", False, False, True))       # GSTIN (Centered)
    
    lines.append((separator_line, False, False, False))
    
    # ─── 2. Metadata Grid or lines ───
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
        # Line-by-line metadata (typical for dhabas/cafes)
        lines.append((f"Date: {date_part}   Time: {time_part}", False, False, False))
        lines.append((f"Bill No: #{receipt_no}     Table: {table_no}", False, False, False))
        lines.append((f"Cashier: {server_name}", False, False, False))
    
    lines.append((separator_line, False, False, False))
    
    # ─── 3. Table Header (Item, Qty, Price, Amount) ───
    table_header = f"{'Item':<16}{'Qty.':^8}{'Price':>9}{'Amount':>9}"
    lines.append((table_header, True, False, False))
    
    lines.append((separator_line, False, False, False))
    
    # ─── 4. Item Rows ───
    total_qty = 0
    for name, qty, price in items:
        qty_str = str(qty)
        amount = qty * price
        total_qty += qty
        
        name_fmt = name[:15]
        row = f"{name_fmt:<16}{qty_str:^8}{price:>9.2f}{amount:>9.2f}"
        lines.append((row, False, False, False))
        
    lines.append((separator_line, False, False, False))
    
    # ─── 5. Summary Section ───
    qty_label = f"Total Qty: {total_qty}"
    subtotal_val = f"{'Sub Total:':<12}{subtotal:>9.2f}"
    lines.append((f"{qty_label:<21}{subtotal_val}", False, False, False))
    
    # Include GST lines if the store utilizes GST tax
    if store.get("has_gst", True) and tax > 0:
        cgst_val = f"{f'CGST {tax_rate*100/2:.1f}%:':<12}{tax/2:>9.2f}"
        sgst_val = f"{f'SGST {tax_rate*100/2:.1f}%:':<12}{tax/2:>9.2f}"
        lines.append((f"{'':<21}{cgst_val}", False, False, False))
        lines.append((f"{'':<21}{sgst_val}", False, False, False))
        
        # Round off
        rounded_total = float(round(total))
        round_off = rounded_total - total
        round_val = f"{'Round off:':<12}{round_off:>9.2f}"
        lines.append((f"{'':<21}{round_val}", False, False, False))
        grand_total = rounded_total
    else:
        grand_total = subtotal
        
    # Grand Total row (centered bold)
    grand_str = f"Grand Total:  ₹ {grand_total:.2f}"
    lines.append((grand_str, True, False, True))
    
    lines.append((separator_line, False, False, False))
    
    # ─── 6. Footer message (centered bold) ───
    lines.append((footer_msg, True, False, True))
    lines.append((separator_line, False, False, False))
    
    # Measure total height needed dynamically based on font size
    font_reg = get_font(13, bold=False)
    font_bold = get_font(13, bold=True)
    font_large_bold = get_font(16, bold=True)
    
    line_h = 19
    padding = 35
    total_height = padding * 2
    
    for _, _, is_large, _ in lines:
        total_height += 23 if is_large else line_h
        
    # Enforce 3:4 Aspect Ratio (width = height * 3 / 4)
    width = total_height * 3 // 4
    
    # Create the canvas using the striped background directly
    canvas = generate_striped_background(width, total_height)
    draw = ImageDraw.Draw(canvas)
    
    # Center standard text blocks horizontally (Roboto Mono 13 size text block is ~336px wide)
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
            # Exact pixel-based text width calculation for perfect visual centering
            text_w = draw.textlength(line_text, font=font)
            x = (width - text_w) // 2
            draw.text((x, y), line_text, font=font, fill=text_color)
        else:
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
