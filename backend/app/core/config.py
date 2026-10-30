import os
from pydantic_settings import BaseSettings

DEFAULT_SECRET_KEY = "deposafe-super-secret-key-sih-2024-grand-finale-aicte-secure"
DEFAULT_BANK_KEY = "deposafe-simulated-sfms-secret-key-2026"

class Settings(BaseSettings):
    PROJECT_NAME: str = "DepoSafe"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Deployment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    RENDER: bool = os.getenv("RENDER", "false").lower() in ("true", "1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Data & Storage
    DATA_DIR: str = os.getenv("DATA_DIR", ".")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "")
    
    # Security & Cryptography
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    BANK_SIGNING_KEY: str = os.getenv("BANK_SIGNING_KEY", DEFAULT_BANK_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,*")
    
    # Bank verification
    ENABLE_BANK_SIMULATOR: bool = True
    SIMULATION_DISCLAIMER: str = "SIMULATED, not a real bank verification"
    
    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            db_path = os.path.abspath(os.path.join(self.DATA_DIR, "deposafe.db"))
            self.DATABASE_URL = f"sqlite:///{db_path}"
        if not self.STORAGE_DIR:
            self.STORAGE_DIR = os.path.abspath(os.path.join(self.DATA_DIR, "storage"))

    def get_cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_production_secrets(self):
        """Enforces security boundaries in production."""
        is_prod = self.ENVIRONMENT.lower() in ("production", "prod") or self.RENDER
        if is_prod:
            if self.SECRET_KEY == DEFAULT_SECRET_KEY:
                raise RuntimeError(
                    "FATAL SECURITY VIOLATION: Refusing to start in production with default SECRET_KEY! "
                    "Configure a strong random SECRET_KEY in the environment."
                )
            if self.BANK_SIGNING_KEY == DEFAULT_BANK_KEY:
                raise RuntimeError(
                    "FATAL SECURITY VIOLATION: Refusing to start in production with default BANK_SIGNING_KEY! "
                    "Configure a strong random BANK_SIGNING_KEY in the environment."
                )

    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
