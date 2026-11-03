import json
import re
from typing import Optional
from bs4 import BeautifulSoup
from scraper.base import BaseScraper, ScrapeResult

class GenericECommerceParser(BaseScraper):
    """
    Intelligent scraper parser that uses Schema.org JSON-LD,
    OpenGraph metadata, and standard CSS selectors to extract product details.
    """

    def scrape(self, url: str) -> ScrapeResult:
        html, error = self.fetch_html(url)
        if error or not html:
            return ScrapeResult(url=url, success=False, error=error)

        soup = BeautifulSoup(html, "lxml")

        # 1. Try structured data (JSON-LD - Schema.org)
        result = self._parse_json_ld(soup, url)
        if result and result.price is not None:
            return result

        # 2. Try OpenGraph / Meta Tags
        result = self._parse_meta_tags(soup, url)
        if result and result.price is not None:
            return result

        # 3. Fallback: Common CSS Selectors
        result = self._parse_css_selectors(soup, url)
        if result and result.price is not None:
            return result

        # Title fallback if we found something
        title = self._extract_title(soup)
        return ScrapeResult(
            url=url,
            title=title,
            success=False,
            error="Could not reliably locate price element using standard e-commerce patterns."
        )

    def _clean_price(self, text: str) -> Optional[float]:
        """Strips symbols, commas, and converts text into a clean float."""
        if not text:
            return None
        # Match digits with optional decimal: e.g. 1,499.99 or 2500
        match = re.search(r"(\d[\d,]*\.?\d*)", text.replace(" ", ""))
        if match:
            clean_str = match.group(1).replace(",", "")
            try:
                val = float(clean_str)
                return val if val > 0 else None
            except ValueError:
                return None
        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extracts the best product title from tags."""
        # Check og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Check h1
        h1 = soup.find("h1")
        if h1 and h1.text.strip():
            return h1.text.strip()

        # Check title tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        return "Unknown Product"

    def _parse_json_ld(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        """Extracts price and details from schema.org JSON-LD blocks."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                # Could be a single dict or a list of items
                items = data if isinstance(data, list) else [data]
                for item in items:
                    item_type = item.get("@type", "")
                    if item_type in ("Product", "IndividualProduct"):
                        title = item.get("name") or self._extract_title(soup)
                        offers = item.get("offers", {})
                        if isinstance(offers, list) and offers:
                            offers = offers[0]
                        price_raw = offers.get("price") or offers.get("lowPrice")
                        currency = offers.get("priceCurrency", "PKR")
                        availability = str(offers.get("availability", "")).lower()
                        in_stock = "outofstock" not in availability

                        clean_p = self._clean_price(str(price_raw))
                        if clean_p is not None:
                            return ScrapeResult(
                                url=url,
                                title=title,
                                price=clean_p,
                                currency=currency,
                                in_stock=in_stock,
                                success=True
                            )
            except Exception:
                continue
        return None

    def _parse_meta_tags(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        """Extracts price from standard OpenGraph / product meta tags."""
        price_tag = (
            soup.find("meta", property="product:price:amount") or
            soup.find("meta", property="og:price:amount") or
            soup.find("meta", attrs={"itemprop": "price"})
        )
        currency_tag = (
            soup.find("meta", property="product:price:currency") or
            soup.find("meta", property="og:price:currency")
        )

        if price_tag and price_tag.get("content"):
            price = self._clean_price(price_tag["content"])
            currency = currency_tag.get("content", "PKR") if currency_tag else "PKR"
            title = self._extract_title(soup)
            if price is not None:
                return ScrapeResult(
                    url=url,
                    title=title,
                    price=price,
                    currency=currency,
                    in_stock=True,
                    success=True
                )
        return None

    def _parse_css_selectors(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        """Extracts using common e-commerce HTML patterns."""
        title = self._extract_title(soup)

        # Selectors commonly used across online stores
        selectors = [
            ".price_color",                 # books.toscrape.com & common templates
            ".product-price",
            ".current-price",
            "[data-price]",
            ".woocommerce-Price-amount",   # WooCommerce
            ".price-item--sale",           # Shopify sale
            ".price-item--regular",        # Shopify regular
            ".a-price .a-offscreen",       # Amazon
            ".pdp-price",                  # Daraz / Lazada
            ".price",
        ]

        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                price = self._clean_price(elem.text)
                if price is not None:
                    # Stock check
                    stock_elem = soup.select_one(".availability, .stock, .in-stock, .instock")
                    in_stock = True
                    if stock_elem and "out" in stock_elem.text.lower():
                        in_stock = False

                    # Currency detect
                    currency = "PKR"
                    if "£" in elem.text:
                        currency = "GBP"
                    elif "$" in elem.text:
                        currency = "USD"
                    elif "€" in elem.text:
                        currency = "EUR"
                    elif "rs" in elem.text.lower():
                        currency = "PKR"

                    return ScrapeResult(
                        url=url,
                        title=title,
                        price=price,
                        currency=currency,
                        in_stock=in_stock,
                        success=True
                    )

        return None

