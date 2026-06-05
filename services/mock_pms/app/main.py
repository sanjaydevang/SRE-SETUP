import json
import logging
import os
import time
from time import monotonic

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "mock-pms")
PORT = int(os.getenv("PORT", "9000"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="Mock PMS", version="1.0.0")

reservations: dict[str, dict] = {}
failure_mode = {"mode": "normal"}
started_at = monotonic()
delivery_success = 0
delivery_failure = 0


class FailureModeRequest(BaseModel):
    mode: str


def log_event(event: str, **fields) -> None:
    logger.info(json.dumps({"service": SERVICE_NAME, "event": event, **fields}, default=str))


@app.get("/health/live")
def live() -> dict:
    return {"status": "live", "service": SERVICE_NAME}


@app.get("/health/ready")
def ready() -> dict:
    return {"status": "ready", "mode": failure_mode["mode"]}


@app.get("/metrics")
def metrics() -> Response:
    uptime = monotonic() - started_at
    body = "\n".join(
        [
            "# HELP crs_pms_uptime_seconds Mock PMS uptime.",
            "# TYPE crs_pms_uptime_seconds gauge",
            f"crs_pms_uptime_seconds {uptime:.0f}",
            "# HELP crs_pms_delivery_success_total PMS accepted deliveries.",
            "# TYPE crs_pms_delivery_success_total counter",
            f"crs_pms_delivery_success_total {delivery_success}",
            "# HELP crs_pms_delivery_failure_total PMS rejected deliveries.",
            "# TYPE crs_pms_delivery_failure_total counter",
            f"crs_pms_delivery_failure_total {delivery_failure}",
            "",
        ]
    )
    return Response(body, media_type="text/plain")


@app.post("/admin/failure-mode")
def set_failure_mode(request: FailureModeRequest) -> dict:
    allowed = {"normal", "slow", "unauthorized", "silent_failure", "server_error"}
    if request.mode not in allowed:
        raise HTTPException(status_code=400, detail=f"mode must be one of {sorted(allowed)}")
    failure_mode["mode"] = request.mode
    log_event("failure_mode_changed", mode=request.mode)
    return {"mode": request.mode}


@app.post("/pms/reservations")
def receive_reservation(payload: dict) -> dict:
    global delivery_success, delivery_failure

    mode = failure_mode["mode"]
    confirmation_id = payload.get("confirmation_id", "unknown")

    if mode == "slow":
        time.sleep(5)
    if mode == "unauthorized":
        delivery_failure += 1
        log_event("pms_delivery_rejected", mode=mode, confirmation_id=confirmation_id)
        raise HTTPException(status_code=401, detail="invalid PMS credential")
    if mode == "server_error":
        delivery_failure += 1
        log_event("pms_delivery_rejected", mode=mode, confirmation_id=confirmation_id)
        raise HTTPException(status_code=500, detail="PMS unavailable")
    if mode == "silent_failure":
        delivery_failure += 1
        log_event("pms_silent_failure", confirmation_id=confirmation_id)
        return {"accepted": True, "stored": False, "warning": "simulated silent failure"}

    reservations[confirmation_id] = payload
    delivery_success += 1
    log_event("pms_reservation_stored", confirmation_id=confirmation_id, property_id=payload.get("property_id"))
    return {"accepted": True, "stored": True, "confirmation_id": confirmation_id}


@app.get("/pms/reservations/{confirmation_id}")
def get_pms_reservation(confirmation_id: str) -> dict:
    reservation = reservations.get(confirmation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="reservation not found in PMS")
    return reservation


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)

