from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from database import Base

class Product(Base):
    """Represents a product item being tracked."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), default="General")
    target_price = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tracked_urls = relationship("TrackedURL", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', target_price={self.target_price})>"


class TrackedURL(Base):
    """Represents a retailer / competitor link for a specific product."""
    __tablename__ = "tracked_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_name = Column(String(100), nullable=False)  # e.g., 'Daraz', 'Amazon', 'PriceOye'
    url = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="tracked_urls")
    price_history = relationship("PriceHistory", back_populates="tracked_url", cascade="all, delete-orphan", order_by="desc(PriceHistory.recorded_at)")

    def __repr__(self):
        return f"<TrackedURL(id={self.id}, store='{self.store_name}', product_id={self.product_id})>"


class PriceHistory(Base):
    """Time-series record of price snapshots collected by the scraper."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracked_url_id = Column(Integer, ForeignKey("tracked_urls.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="PKR")
    in_stock = Column(Boolean, default=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tracked_url = relationship("TrackedURL", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(id={self.id}, price={self.price} {self.currency}, recorded_at={self.recorded_at})>"


class PriceAlert(Base):
    """User-configured threshold for price drop notifications."""
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    alert_price = Column(Numeric(10, 2), nullable=False)
    email = Column(String(255), nullable=True)
    is_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="alerts")

    def __repr__(self):
        return f"<PriceAlert(product_id={self.product_id}, alert_price={self.alert_price}, triggered={self.is_triggered})>"

