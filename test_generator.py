import os
from generator import generate_receipt_image

def main():
    print("Testing receipt generator...")
    os.makedirs("test_output", exist_ok=True)
    
    templates = ["grocery", "cafe", "retail", "gas"]
    realism_modes = ["clean", "thermal", "tabletop"]
    
    # Let's generate a combination of layouts and realism modes
    count = 1
    for template in templates:
        for realism in realism_modes:
            output_path = f"test_output/{count}_{template}_{realism}.png"
            print(f"Generating {template} ({realism}) -> {output_path}...")
            try:
                img = generate_receipt_image(
                    template=template,
                    realism=realism,
                    currency="USD",
                    font="receipt"
                )
                img.save(output_path)
                print(f"Saved successfully.")
                count += 1
            except Exception as e:
                print(f"Error generating {template} ({realism}): {e}")
                import traceback
                traceback.print_exc()

    print(f"\nDone! All test images saved to the 'test_output' directory.")

if __name__ == "__main__":
    main()
