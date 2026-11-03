# 🛒 Smart E-Commerce Price Tracker & Competitor Scraper

A robust, production-ready Python application that monitors e-commerce product prices across multiple competitors, detects stock changes, and stores historical price fluctuations in **MySQL**.

Built with strict adherence to **Legal, Ethical, and Halal Web Scraping** practices.

---

## 📜 Legal & Halal Scraping Principles Implemented

This project strictly follows ethical web scraping guidelines:
1. **Robots.txt Adherence (`robots_checker.py`):** Automatically reads and verifies target website `/robots.txt` before sending any request. If scraping is disallowed, the URL is rejected.
2. **Polite Crawling & Rate Limiting (`scraper/base.py`):** Enforces rate-limiting and sleep delays between requests (default: 3 seconds) to prevent overloading servers.
3. **Public Data Only:** Scrapes only publicly accessible product titles and prices. Never bypasses logins, authentication, or paywalls.
4. **Transparent User-Agent:** Identifies the bot clearly in HTTP headers (`SmartPriceBot/1.0`).

---

## 🏗️ Project Architecture

```
Laravel Project/
│
├── .env                  # MySQL credentials & scraping configurations
├── config.py             # Configuration loader
├── database.py           # SQLAlchemy MySQL engine & session management
├── models.py             # Product, TrackedURL, PriceHistory, PriceAlert
├── robots_checker.py     # Ethical robots.txt validator
├── schema.sql            # MySQL schema reference
├── service.py            # Business logic (scraping, history, price alerts)
├── scheduler.py          # Background task runner (periodic price monitoring)
├── main.py               # Interactive CLI dashboard
├── requirements.txt      # Python dependencies
└── scraper/
    ├── __init__.py
    ├── base.py           # Rate-limiting, headers & HTTP client
    └── parser.py         # Schema.org JSON-LD, OpenGraph & CSS selectors
```

---

## 🗄️ MySQL Database Setup

The application automatically connects to MySQL and creates `price_tracker_db` and all required tables:
* `products`: Main tracked products
* `tracked_urls`: Retailer & competitor links for each product
* `price_history`: Historical price points with timestamps
* `price_alerts`: Alert triggers when price drops below threshold

Configure your MySQL credentials in `.env`:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=price_tracker_db
```

---

## 🚀 How to Run

### 1. Launch the Interactive Dashboard
```bash
.\venv\Scripts\python main.py
```
Menu Options:
* `1. 📋 View All Products & Competitor Prices`
* `2. ➕ Add New Product & Competitor URL` (Live robots.txt check)
* `3. ⚡ Run Scraper Now` (Live fetch & MySQL insert)
* `4. 📈 View Historical Price Fluctuations`
* `5. 🌱 Seed Demo E-Commerce Products`
* `6. 🕒 Run Scheduled Background Monitoring`
* `7. 🚪 Exit`

### 2. Run Automated Background Scraping
To run periodic price checks (e.g. every 30 or 60 minutes):
```bash
.\venv\Scripts\python scheduler.py
```

