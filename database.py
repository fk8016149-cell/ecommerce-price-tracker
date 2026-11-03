import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import config

# Base class for SQLAlchemy ORM models
Base = declarative_base()

def ensure_database_exists():
    """Connects to MySQL server and creates the target database if not present."""
    try:
        conn = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Could not initialize MySQL database '{config.DB_NAME}': {e}")
        raise

# Ensure database exists before creating engine
ensure_database_exists()

# Create SQLAlchemy Engine
engine = create_engine(
    config.get_db_url(with_db=True),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates all tables defined in models.py."""
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency / context manager for DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

