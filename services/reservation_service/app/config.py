import os


class Settings:
    service_name = os.getenv("SERVICE_NAME", "reservation-service")
    port = int(os.getenv("PORT", "8000"))
    database_url = os.getenv("DATABASE_URL", "postgresql://crs:crs_password@localhost:5432/crs")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    reservation_stream = os.getenv("RESERVATION_STREAM", "reservation-events")


settings = Settings()

