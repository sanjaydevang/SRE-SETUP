import os


class Settings:
    service_name = os.getenv("SERVICE_NAME", "notification-worker")
    port = int(os.getenv("PORT", "8100"))
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    reservation_stream = os.getenv("RESERVATION_STREAM", "reservation-events")
    reservation_group = os.getenv("RESERVATION_GROUP", "pms-delivery-workers")
    consumer_name = os.getenv("CONSUMER_NAME", "worker-1")
    pms_base_url = os.getenv("PMS_BASE_URL", "http://localhost:9000")
    max_delivery_attempts = int(os.getenv("MAX_DELIVERY_ATTEMPTS", "3"))
    dlq_stream = os.getenv("DLQ_STREAM", "reservation-events-dlq")


settings = Settings()

