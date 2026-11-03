import sys

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from decimal import Decimal
from tabulate import tabulate
from database import init_db, SessionLocal
from models import Product, TrackedURL, PriceHistory, PriceAlert
import service

def print_header():
    print("\n" + "=" * 65)
    print("   [+] SMART E-COMMERCE PRICE TRACKER & COMPETITOR SCRAPER")
    print("   Database: MySQL | Scraper: Legal, Halal & Ethical")
    print("=" * 65)

def list_products():
    summary = service.get_products_summary()
    if not summary:
        print("\n[i] No products tracked yet. Choose option 2 or 5 to add products.")
        return

    table_data = []
    for p in summary:
        best_price_str = f"{p['lowest_price']} ({p['best_store']})" if p['lowest_price'] else "Not Scraped Yet"
        table_data.append([
            p["id"],
            p["name"][:30],
            p["category"],
            p["target_price"] or "N/A",
            p["competitors_count"],
            best_price_str
        ])

    headers = ["ID", "Product Name", "Category", "Target Price", "Competitors", "Best Current Price"]
    print("\n[PRODUCTS] TRACKED PRODUCTS:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Also show details for each store
    for p in summary:
        if p["stores"]:
            print(f"\n--> Competitor breakdown for #{p['id']} - {p['name']}:")
            store_rows = [
                [s["store"], f"{s['currency']} {s['current_price']}" if s['current_price'] else "Pending", "In Stock" if s['in_stock'] else "Out of Stock", s['last_scraped']]
                for s in p["stores"]
            ]
            print(tabulate(store_rows, headers=["Store", "Latest Price", "Stock Status", "Last Scraped"], tablefmt="simple"))

def add_product_menu():
    print("\n--- Add New Product ---")
    name = input("Enter Product Name: ").strip()
    if not name:
        print("[!] Product name cannot be empty.")
        return

    category = input("Enter Category (e.g., Electronics, Books, Fashion) [General]: ").strip() or "General"
    target_price_input = input("Enter your Target Alert Price (or press Enter to skip): ").strip()
    target_price = float(target_price_input) if target_price_input else None

    product = service.create_product(name=name, category=category, target_price=target_price)
    print(f"[OK] Product created with ID #{product.id}!")

    add_url = input("Do you want to add a competitor URL for this product now? (y/n): ").strip().lower()
    if add_url == "y":
        store_name = input("Enter Store Name (e.g. Daraz, PriceOye, Amazon): ").strip() or "Store"
        url = input("Enter Product Webpage URL: ").strip()

        print("[*] Checking website policy (robots.txt) for ethical compliance...")
        tracked, msg = service.add_tracked_url(product_id=product.id, store_name=store_name, url=url)
        print(msg)

def scrape_now():
    print("\n[*] Starting ethical scrape across all active competitor URLs...")
    results = service.scrape_all_active()
    if not results:
        print("[i] No active URLs found to scrape.")
        return

    rows = []
    for r in results:
        if r.get("success"):
            rows.append([r["store"], r["title"][:28], f"{r['currency']} {r['price']}", "Yes" if r['in_stock'] else "No", "Success"])
        else:
            rows.append([r.get("store", "Unknown"), "N/A", "N/A", "N/A", f"Error: {r.get('error')}"])

    print("\n[RESULTS] SCRAPING RESULTS (Saved to MySQL):")
    print(tabulate(rows, headers=["Store", "Product Title", "Price", "In Stock", "Status"], tablefmt="grid"))

def view_price_history():
    with SessionLocal() as db:
        products = db.query(Product).all()
        if not products:
            print("[i] No products in database.")
            return

        print("\nAvailable Products:")
        for p in products:
            print(f"[{p.id}] {p.name}")

    pid = input("\nEnter Product ID to view history: ").strip()
    if not pid.isdigit():
        print("[!] Invalid ID.")
        return

    with SessionLocal() as db:
        product = db.query(Product).filter(Product.id == int(pid)).first()
        if not product:
            print("[!] Product not found.")
            return

        rows = []
        for url in product.tracked_urls:
            for h in url.price_history:
                rows.append([
                    url.store_name,
                    f"{h.currency} {h.price}",
                    "In Stock" if h.in_stock else "Out of Stock",
                    h.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
                ])

        if not rows:
            print("[i] No price records yet. Run option 3 to scrape.")
        else:
            print(f"\n[HISTORY] Price History for: {product.name}")
            print(tabulate(rows, headers=["Store", "Price", "Availability", "Recorded At"], tablefmt="grid"))

def seed_demo_data():
    """Adds ethical, public sample products (using books.toscrape.com, an official scraping practice sandbox)."""
    print("\n[*] Seeding compliant demo e-commerce products into MySQL...")

    # Demo Product 1
    p1 = service.create_product(name="A Light in the Attic", category="Books", target_price=50.00)
    service.add_tracked_url(
        product_id=p1.id,
        store_name="Demo Store A",
        url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )

    # Demo Product 2
    p2 = service.create_product(name="Tipping the Velvet", category="Books", target_price=45.00)
    service.add_tracked_url(
        product_id=p2.id,
        store_name="Demo Store B",
        url="https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
    )

    print("[OK] Demo products & competitor URLs added successfully!")
    print("Now select Option 3 to scrape their live prices into MySQL.")

def main():
    # Initialize MySQL Tables
    init_db()

    while True:
        print_header()
        print("1. [View] All Products & Competitor Prices")
        print("2. [Add] New Product & Competitor URL")
        print("3. [Scrape] Run Scraper Now (Live Fetch & Store in MySQL)")
        print("4. [History] View Historical Price Fluctuations")
        print("5. [Demo] Seed Demo E-Commerce Products (Ready-to-test)")
        print("6. [Schedule] Run Scheduled Background Monitoring")
        print("7. [Exit] Exit")
        print("-" * 65)

        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            list_products()
        elif choice == "2":
            add_product_menu()
        elif choice == "3":
            scrape_now()
        elif choice == "4":
            view_price_history()
        elif choice == "5":
            seed_demo_data()
        elif choice == "6":
            from scheduler import start_scheduler
            interval = input("Check interval in minutes [default 30]: ").strip()
            mins = int(interval) if interval.isdigit() else 30
            start_scheduler(interval_minutes=mins)
        elif choice == "7":
            print("\nKhuda Hafiz! Exiting Smart Price Tracker.")
            sys.exit(0)
        else:
            print("[!] Invalid option, please choose between 1 and 7.")

if __name__ == "__main__":
    main()


