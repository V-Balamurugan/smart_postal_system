from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "link_to_your_default_database")

    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    ORS_API_KEY = os.getenv("ORS_API_KEY", "your-ors-api-key-change-this-in-production")

settings = Settings()