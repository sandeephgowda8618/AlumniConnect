"""AlumniConnect Core Configuration
Loads environment settings, security keys, database parameters, recommendation defaults,
and Redis namespace policies according to authoritative project specifications.
"""

import os
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_DB = str(BACKEND_DIR / "alumniconnect.db")


class Settings(BaseSettings):
    PROJECT_NAME: str = "AlumniConnect"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "dev"

    # Security & JWT
    SECRET_KEY: str = "alumniconnect-secret-key-production-grade-random-string-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Authoritative MySQL Relational Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "alumniconnect"
    
    # Database connection URL (defaults to a high-fidelity local SQLite engine for offline sandbox,
    # or connects to MySQL when configured)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_DB}")

    # Supporting Redis Store
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_KEY_PREFIX: str = "ac:dev:v1:"

    # Supporting Neo4j Graph Store
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "alumniconnect"

    # Recommendation Engine Configurable Defaults (Recommendation Design §7)
    WEIGHT_SKILL: float = 0.30
    WEIGHT_DOMAIN: float = 0.20
    WEIGHT_EXPERIENCE: float = 0.15
    WEIGHT_CAREER: float = 0.20
    WEIGHT_QUALITY: float = 0.15
    TARGET_EXPERIENCE_YEARS: float = 5.0
    BAYESIAN_PRIOR_M: float = 5.0
    PLATFORM_AVERAGE_RATING: float = 4.0
    GATE_CAPACITY: bool = True

    # Booking & Scheduling Policies (Business Rules Catalogue BR-T16, SP02)
    BOOKING_CANCELLATION_CUTOFF_HOURS: int = 2
    DEFAULT_MAX_ACTIVE_MENTEES: int = 2
    REOPEN_SLOT_ON_CANCELLATION: bool = True

    # Outbox & Notification Policies
    OUTBOX_BATCH_SIZE: int = 20
    OUTBOX_MAX_RETRIES: int = 5
    OUTBOX_POLL_INTERVAL_SECONDS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

