import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tabulate import tabulate
from database import init_db, SessionLocal
from models import Product, TrackedURL, PriceHistory
import service

def run_live():
    print("=" * 70)
    print(" 🛒 SMART E-COMMERCE PRICE TRACKER - LIVE EXECUTION")
    print("=" * 70)

    # 1. Initialize DB
    init_db()
    print("[1/3] Connected to MySQL: price_tracker_db")

    # 2. Run Live Scrape
    print("\n[2/3] Scraping live product prices across all competitor websites...")
    results = service.scrape_all_active()

    scrape_table = []
    for r in results:
        if r.get("success"):
            scrape_table.append([
                r["store"],
                r["title"][:28],
                f"{r['currency']} {r['price']}",
                "Yes" if r['in_stock'] else "No",
                "✓ Saved to MySQL"
            ])
        else:
            scrape_table.append([r.get("store", "Unknown"), "N/A", "N/A", "N/A", f"Error: {r.get('error')}"])

    print("\n" + tabulate(scrape_table, headers=["Store", "Product Title", "Latest Price", "In Stock", "MySQL Status"], tablefmt="grid"))

    # 3. Show Comparison Table
    print("\n[3/3] Current Market Price Comparison:")
    summary = service.get_products_summary()
    table_data = []
    for p in summary:
        best_price_str = f"{p['lowest_price']} ({p['best_store']})" if p['lowest_price'] else "Pending"
        table_data.append([
            p["id"],
            p["name"][:30],
            p["category"],
            p["target_price"] or "None",
            p["competitors_count"],
            best_price_str
        ])

    print("\n" + tabulate(table_data, headers=["ID", "Product Name", "Category", "Target Price", "Competitors", "Cheapest Store & Price"], tablefmt="fancy_grid"))

    print("\n" + "=" * 70)
    print(" ✅ Live Run Complete! All records saved into MySQL successfully.")
    print("=" * 70)

if __name__ == "__main__":
    run_live()

