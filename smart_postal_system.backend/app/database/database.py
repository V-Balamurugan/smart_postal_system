from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

<<<<<<< HEAD
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. Check your .env file."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
=======
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Check if PostgreSQL configuration is fully provided
if DB_HOST and DB_PORT and DB_NAME and DB_USER and DB_PASSWORD:
    try:
        DATABASE_URL = (
            f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        print("Attempting to connect to PostgreSQL...")
        # Use a short connection timeout
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 3})
        # Test connection
        with engine.connect() as conn:
            pass
        print("Connected to PostgreSQL successfully.")
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}. Falling back to SQLite database.")
        DATABASE_URL = "sqlite:///./smart_postal.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    print("PostgreSQL connection environment variables are missing. Falling back to SQLite database.")
    DATABASE_URL = "sqlite:///./smart_postal.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
>>>>>>> fbe67239cd358e5338da41924b95b8f47875abbc

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()