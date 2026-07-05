import os
from generator import generate_receipt_image

def main():
    print("Testing Royal Chinese Garden bill generator...")
    os.makedirs("test_output", exist_ok=True)
    
    output_path = "test_output/royal_chinese_garden_bill.png"
    print(f"Generating bill image -> {output_path}...")
    try:
        img, data = generate_receipt_image()
        img.save(output_path)
        print(f"Saved successfully! View the generated bill at {output_path}")
        print(f"Shop name: {data['store_name']}")
        print(f"Address: {data['store_addr']}")
        print(f"Total: {data['total']}")
    except Exception as e:
        print(f"Error generating bill: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
