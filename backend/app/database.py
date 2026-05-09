from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class SavedResult(Base):
    __tablename__ = "saved_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    product_type: Mapped[str] = mapped_column(String(80), index=True)
    shade_name: Mapped[str] = mapped_column(String(100), default="")
    shade_depth: Mapped[str] = mapped_column(String(40), default="")
    undertone: Mapped[str] = mapped_column(String(40), default="")
    depth: Mapped[str] = mapped_column(String(40), default="")
    skin_type_match: Mapped[str] = mapped_column(String(140), default="")
    coverage: Mapped[str] = mapped_column(String(40), default="")
    finish: Mapped[str] = mapped_column(String(80), default="")
    price_tier: Mapped[str] = mapped_column(String(40), default="drugstore", index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    good_for: Mapped[str] = mapped_column(Text, default="")
    avoid_if: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(Text, default="")
    shopping_link: Mapped[str] = mapped_column(Text, default="")
    formula_base: Mapped[str] = mapped_column(String(80), default="")
    best_for: Mapped[str] = mapped_column(Text, default="")
    avoid_pairing_with: Mapped[str] = mapped_column(Text, default="")
    compatibility_notes: Mapped[str] = mapped_column(Text, default="")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    feedback_type: Mapped[str] = mapped_column(String(80), index=True)
    context: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_product_columns()
    from .product_catalog import seed_products

    db = SessionLocal()
    try:
        seed_products(db)
    finally:
        db.close()


def _ensure_product_columns() -> None:
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("products")}
    required = {
        "shade_depth": "VARCHAR(40) DEFAULT ''",
        "price_tier": "VARCHAR(40) DEFAULT 'drugstore'",
        "good_for": "TEXT DEFAULT ''",
        "avoid_if": "TEXT DEFAULT ''",
        "image_url": "TEXT DEFAULT ''",
        "formula_base": "VARCHAR(80) DEFAULT ''",
        "best_for": "TEXT DEFAULT ''",
        "avoid_pairing_with": "TEXT DEFAULT ''",
        "compatibility_notes": "TEXT DEFAULT ''",
    }
    with engine.begin() as connection:
        for column, definition in required.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE products ADD COLUMN {column} {definition}"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
