import os
from generator import (
    generate_receipt_image,
    generate_kfc_exact_replica_receipt,
    generate_bigbasket_exact_replica_invoice,
    generate_lenskart_exact_replica_invoice
)

def main():
    print("Testing Premium Exact Replica Bill Generators...")
    os.makedirs("test_output", exist_ok=True)
    
    # 1. Test KFC Thermal Receipt Replica
    print("Generating KFC Thermal Receipt Replica...")
    kfc_img, kfc_data = generate_kfc_exact_replica_receipt()
    kfc_img.save("test_output/kfc_replica.png")
    print(f"KFC Saved -> test_output/kfc_replica.png (Total: {kfc_data['total']})")
    
    # 2. Test BigBasket A4 Tax Invoice Replica
    print("Generating BigBasket Tax Invoice Replica...")
    bb_img, bb_data = generate_bigbasket_exact_replica_invoice()
    bb_img.save("test_output/bigbasket_replica.png")
    print(f"BigBasket Saved -> test_output/bigbasket_replica.png (Total: {bb_data['total']})")

    # 3. Test Lenskart A4 Tax Invoice Replica
    print("Generating Lenskart Tax Invoice Replica...")
    lk_img, lk_data = generate_lenskart_exact_replica_invoice()
    lk_img.save("test_output/lenskart_replica.png")
    print(f"Lenskart Saved -> test_output/lenskart_replica.png (Total: {lk_data['total']})")

if __name__ == "__main__":
    main()
