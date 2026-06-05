import json
import logging
import uuid
from decimal import Decimal

import redis
import uvicorn
from fastapi import FastAPI, HTTPException, Response

from .config import settings
from .database import database_ready, fetch_reservation, initialize_schema, insert_reservation
from .metrics import metrics
from .models import ReservationRequest, ReservationResponse

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(settings.service_name)

app = FastAPI(title="CRS Reservation Service", version="1.0.0")
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"service": settings.service_name, "event": event, **fields}, default=json_default))


@app.on_event("startup")
def startup() -> None:
    initialize_schema()
    log_event("service_started")


@app.get("/health/live")
def live() -> dict:
    return {"status": "live", "service": settings.service_name}


@app.get("/health/ready")
def ready() -> dict:
    db_ok = database_ready()
    redis_ok = False
    try:
        redis_ok = bool(redis_client.ping())
    except Exception:
        redis_ok = False

    if not db_ok or not redis_ok:
        raise HTTPException(status_code=503, detail={"database": db_ok, "redis": redis_ok})
    return {"status": "ready", "database": db_ok, "redis": redis_ok}


@app.get("/metrics")
def service_metrics() -> Response:
    return Response(metrics.prometheus_text(settings.service_name), media_type="text/plain")


@app.post("/v1/reservations", response_model=ReservationResponse, status_code=201)
def create_reservation(request: ReservationRequest) -> ReservationResponse:
    confirmation_id = f"CRS-{uuid.uuid4().hex[:12].upper()}"

    try:
        insert_reservation(confirmation_id, request)
    except Exception as exc:
        metrics.reservation_errors += 1
        log_event("reservation_db_write_failed", error=str(exc), property_id=request.property_id)
        raise HTTPException(status_code=500, detail="failed to write reservation") from exc

    event = request.model_dump()
    event["confirmation_id"] = confirmation_id
    event["status"] = "CONFIRMED"

    try:
        redis_client.xadd(settings.reservation_stream, {"payload": json.dumps(event, default=json_default)})
    except Exception as exc:
        metrics.queue_publish_errors += 1
        log_event("reservation_queue_publish_failed", error=str(exc), confirmation_id=confirmation_id)
        raise HTTPException(status_code=500, detail="failed to publish reservation event") from exc

    metrics.reservations_created += 1
    log_event(
        "reservation_created",
        confirmation_id=confirmation_id,
        ota_partner=request.ota_partner,
        hotel_chain_id=request.hotel_chain_id,
        property_id=request.property_id,
        hotel_tier=request.hotel_tier.value,
    )

    return ReservationResponse(
        confirmation_id=confirmation_id,
        status="CONFIRMED",
        queue_stream=settings.reservation_stream,
    )


@app.get("/v1/reservations/{confirmation_id}")
def get_reservation(confirmation_id: str) -> dict:
    reservation = fetch_reservation(confirmation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="reservation not found")
    return reservation


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)

