import os
import json
from PIL import Image

def analyze_receipt_style(image_path):
    """
    Analyzes a receipt image to extract its dominant paper (background) color
    and ink (text) color. Returns a dict with these colors.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB and resize to a small thumbnail for speed and noise reduction
            img = img.convert("RGB")
            img_small = img.resize((150, 150))
            
            pixels = list(img_small.getdata())
            
            light_pixels = []
            dark_pixels = []
            
            for r, g, b in pixels:
                # Perceptive luminance formula (rec601)
                luminance = 0.299 * r + 0.587 * g + 0.114 * b
                
                # Pixels with high luminance are background (paper)
                if luminance > 120:
                    light_pixels.append((r, g, b))
                else:
                    dark_pixels.append((r, g, b))
            
            # Compute averages
            if light_pixels:
                avg_bg = [int(sum(x) / len(light_pixels)) for x in zip(*light_pixels)]
            else:
                avg_bg = [245, 245, 242]  # Off-white default
                
            if dark_pixels:
                avg_txt = [int(sum(x) / len(dark_pixels)) for x in zip(*dark_pixels)]
            else:
                avg_txt = [35, 35, 35]  # Charcoal default
                
            # Post-process colors for realism (e.g. ensure background is not too bright, text is dark enough)
            # Ensure background is reasonably light
            bg_lum = 0.299 * avg_bg[0] + 0.587 * avg_bg[1] + 0.114 * avg_bg[2]
            if bg_lum < 160:
                # If background is too dark, scale it up towards light grey
                factor = 180 / max(1, bg_lum)
                avg_bg = [min(255, int(c * factor)) for c in avg_bg]
                
            # Ensure text is dark enough to be legible
            txt_lum = 0.299 * avg_txt[0] + 0.587 * avg_txt[1] + 0.114 * avg_txt[2]
            if txt_lum > 100:
                # Scale it down towards black
                factor = 40 / max(1, txt_lum)
                avg_txt = [max(0, int(c * factor)) for c in avg_txt]
                
            return {
                "bg_color": tuple(avg_bg),
                "text_color": tuple(avg_txt),
                "detected": True
            }
            
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return {
            "bg_color": (245, 245, 240),
            "text_color": (35, 35, 35),
            "detected": False
        }

def save_user_style(chat_id, style_data, styles_dir="styles"):
    os.makedirs(styles_dir, exist_ok=True)
    style_path = os.path.join(styles_dir, f"{chat_id}_style.json")
    with open(style_path, "w") as f:
        json.dump(style_data, f, indent=4)

def load_user_style(chat_id, styles_dir="styles"):
    style_path = os.path.join(styles_dir, f"{chat_id}_style.json")
    if os.path.exists(style_path):
        try:
            with open(style_path, "r") as f:
                data = json.load(f)
                # Convert list back to tuple
                data["bg_color"] = tuple(data["bg_color"])
                data["text_color"] = tuple(data["text_color"])
                return data
        except Exception:
            pass
    return None
