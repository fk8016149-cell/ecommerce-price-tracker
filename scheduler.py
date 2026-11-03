import sys
import time
import schedule
from datetime import datetime
from service import scrape_all_active

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def job():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Running scheduled price scraper...")
    results = scrape_all_active()
    for r in results:
        if r.get("success"):
            print(f"  ✓ [{r['store']}] {r['title']} -> {r['currency']} {r['price']} (Stock: {'Yes' if r['in_stock'] else 'No'})")
        else:
            print(f"  ✗ [{r.get('store', 'Unknown')}] Error: {r.get('error')}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Done. Next check scheduled.")

def start_scheduler(interval_minutes: int = 60):
    print(f"==================================================")
    print(f"🕒 E-Commerce Scraper Scheduler Started")
    print(f"Interval: Every {interval_minutes} minute(s)")
    print(f"Ethical scraping rules enforced.")
    print(f"Press Ctrl+C to stop.")
    print(f"==================================================")

    # Run once immediately
    job()

    # Schedule subsequent runs
    schedule.every(interval_minutes).minutes.do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user.")

if __name__ == "__main__":
    start_scheduler(interval_minutes=30)

