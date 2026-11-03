import sys
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, TrackedURL, PriceHistory, PriceAlert
from scraper.parser import GenericECommerceParser
from robots_checker import can_fetch_url

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

parser = GenericECommerceParser()

def create_product(name: str, category: str = "General", target_price: float = None) -> Product:
    """Adds a new product to track in the database."""
    with SessionLocal() as db:
        product = Product(
            name=name,
            category=category,
            target_price=Decimal(str(target_price)) if target_price else None
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

def add_tracked_url(product_id: int, store_name: str, url: str) -> tuple[TrackedURL, str]:
    """
    Adds a competitor/retailer URL after checking robots.txt ethical compliance.
    """
    # Ethical Check
    allowed, message = can_fetch_url(url)
    if not allowed:
        return None, f"[Ethical/Legal Guard] Cannot track URL: {message}"

    with SessionLocal() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None, f"Product ID {product_id} not found."

        tracked = TrackedURL(
            product_id=product_id,
            store_name=store_name,
            url=url,
            is_active=True
        )
        db.add(tracked)
        db.commit()
        db.refresh(tracked)
        return tracked, "Success: URL added and verified with website policy."

def record_price(db: Session, tracked_url_id: int, price: float, currency: str, in_stock: bool) -> PriceHistory:
    """Inserts a new price snapshot into price_history table."""
    history = PriceHistory(
        tracked_url_id=tracked_url_id,
        price=Decimal(str(price)),
        currency=currency,
        in_stock=in_stock,
        recorded_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def check_alerts(db: Session, product_id: int, latest_price: float):
    """Checks if current price meets or drops below user alert threshold."""
    alerts = db.query(PriceAlert).filter(
        PriceAlert.product_id == product_id,
        PriceAlert.is_triggered == False,
        PriceAlert.alert_price >= Decimal(str(latest_price))
    ).all()

    for alert in alerts:
        print(f"\n🔔 [PRICE DROP ALERT!] Product #{product_id} dropped to {latest_price}! Target was {alert.alert_price}")
        alert.is_triggered = True
    if alerts:
        db.commit()

def scrape_single_url(tracked_url_id: int) -> dict:
    """Scrapes a specific tracked URL and records the result."""
    with SessionLocal() as db:
        tracked = db.query(TrackedURL).filter(TrackedURL.id == tracked_url_id).first()
        if not tracked:
            return {"success": False, "error": "Tracked URL not found"}

        result = parser.scrape(tracked.url)
        if result.success and result.price is not None:
            # Update last scraped timestamp
            tracked.last_scraped_at = datetime.utcnow()
            db.commit()

            # Record in history
            record = record_price(
                db=db,
                tracked_url_id=tracked.id,
                price=result.price,
                currency=result.currency,
                in_stock=result.in_stock
            )

            # Check alerts
            check_alerts(db, tracked.product_id, result.price)

            return {
                "success": True,
                "store": tracked.store_name,
                "title": result.title,
                "price": result.price,
                "currency": result.currency,
                "in_stock": result.in_stock,
                "recorded_at": record.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "success": False,
                "store": tracked.store_name,
                "error": result.error or "Failed to extract price"
            }

def scrape_all_active() -> list[dict]:
    """Ethically iterates through all active tracked URLs with rate limiting."""
    results = []
    with SessionLocal() as db:
        active_urls = db.query(TrackedURL).filter(TrackedURL.is_active == True).all()
        url_ids = [u.id for u in active_urls]

    for uid in url_ids:
        res = scrape_single_url(uid)
        results.append(res)
    return results

def get_products_summary() -> list[dict]:
    """Fetches all products with latest price comparison across competitors."""
    with SessionLocal() as db:
        products = db.query(Product).all()
        summary = []
        for p in products:
            urls_data = []
            lowest_price = None
            cheapest_store = None

            for u in p.tracked_urls:
                latest_history = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.tracked_url_id == u.id)
                    .order_by(PriceHistory.recorded_at.desc())
                    .first()
                )
                curr_price = float(latest_history.price) if latest_history else None
                curr_curr = latest_history.currency if latest_history else "PKR"
                in_stock = latest_history.in_stock if latest_history else None

                if curr_price is not None:
                    if lowest_price is None or curr_price < lowest_price:
                        lowest_price = curr_price
                        cheapest_store = u.store_name

                urls_data.append({
                    "store": u.store_name,
                    "url": u.url,
                    "current_price": curr_price,
                    "currency": curr_curr,
                    "in_stock": in_stock,
                    "last_scraped": u.last_scraped_at.strftime("%Y-%m-%d %H:%M") if u.last_scraped_at else "Never"
                })

            summary.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "target_price": float(p.target_price) if p.target_price else None,
                "lowest_price": lowest_price,
                "best_store": cheapest_store,
                "competitors_count": len(p.tracked_urls),
                "stores": urls_data
            })
        return summary

