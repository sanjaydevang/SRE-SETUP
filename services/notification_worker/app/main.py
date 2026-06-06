import asyncio
import json
import logging
from time import monotonic

import httpx
import redis
import uvicorn
from fastapi import FastAPI, HTTPException, Response

from .config import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(settings.service_name)

app = FastAPI(title="CRS Notification Worker", version="1.0.0")
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
started_at = monotonic()

delivery_success = 0
delivery_failure = 0
dlq_messages = 0
worker_running = False


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"service": settings.service_name, "event": event, **fields}, default=str))


def ensure_consumer_group() -> None:
    try:
        redis_client.xgroup_create(settings.reservation_stream, settings.reservation_group, id="0", mkstream=True)
        log_event("consumer_group_created", stream=settings.reservation_stream, group=settings.reservation_group)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def deliver_to_pms(payload: dict) -> bool:
    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.post(f"{settings.pms_base_url}/pms/reservations", json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"PMS returned HTTP {response.status_code}: {response.text}")

        body = response.json()
        if body.get("stored") is False:
            raise RuntimeError("PMS returned success status but did not store reservation")
        return True


async def process_message(message_id: str, fields: dict) -> None:
    global delivery_success, delivery_failure, dlq_messages

    payload = json.loads(fields["payload"])
    attempts = int(fields.get("attempts", "0")) + 1
    confirmation_id = payload.get("confirmation_id")

    try:
        await deliver_to_pms(payload)
        redis_client.xack(settings.reservation_stream, settings.reservation_group, message_id)
        delivery_success += 1
        log_event("pms_delivery_success", confirmation_id=confirmation_id, attempts=attempts)
    except Exception as exc:
        delivery_failure += 1
        log_event("pms_delivery_failed", confirmation_id=confirmation_id, attempts=attempts, error=str(exc))

        redis_client.xack(settings.reservation_stream, settings.reservation_group, message_id)
        if attempts >= settings.max_delivery_attempts:
            redis_client.xadd(settings.dlq_stream, {"payload": json.dumps(payload), "error": str(exc)})
            dlq_messages += 1
            log_event("message_sent_to_dlq", confirmation_id=confirmation_id, dlq_stream=settings.dlq_stream)
        else:
            redis_client.xadd(settings.reservation_stream, {"payload": json.dumps(payload), "attempts": str(attempts)})


async def worker_loop() -> None:
    global worker_running
    worker_running = True
    ensure_consumer_group()
    log_event("worker_started")

    while True:
        try:
            response = await asyncio.to_thread(
                redis_client.xreadgroup,
                settings.reservation_group,
                settings.consumer_name,
                {settings.reservation_stream: ">"},
                count=5,
                block=1000,
            )
            for _, messages in response:
                for message_id, fields in messages:
                    await process_message(message_id, fields)
        except Exception as exc:
            log_event("worker_loop_error", error=str(exc))
            await asyncio.sleep(2)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(worker_loop())


@app.get("/health/live")
def live() -> dict:
    return {"status": "live", "service": settings.service_name}


@app.get("/health/ready")
def ready() -> dict:
    redis_ok = False
    try:
        redis_ok = bool(redis_client.ping())
    except Exception:
        redis_ok = False
    if not redis_ok or not worker_running:
        raise HTTPException(status_code=503, detail={"redis": redis_ok, "worker_running": worker_running})
    return {"status": "ready", "redis": redis_ok, "worker_running": worker_running}


@app.get("/metrics")
def metrics() -> Response:
    uptime = monotonic() - started_at
    body = "\n".join(
        [
            "# HELP crs_worker_uptime_seconds Notification worker uptime.",
            "# TYPE crs_worker_uptime_seconds gauge",
            f"crs_worker_uptime_seconds {uptime:.0f}",
            "# HELP crs_pms_delivery_success_total Successful PMS deliveries.",
            "# TYPE crs_pms_delivery_success_total counter",
            f"crs_pms_delivery_success_total {delivery_success}",
            "# HELP crs_pms_delivery_failure_total Failed PMS deliveries.",
            "# TYPE crs_pms_delivery_failure_total counter",
            f"crs_pms_delivery_failure_total {delivery_failure}",
            "# HELP crs_dlq_messages_total Messages sent to DLQ.",
            "# TYPE crs_dlq_messages_total counter",
            f"crs_dlq_messages_total {dlq_messages}",
            "",
        ]
    )
    return Response(body, media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)
