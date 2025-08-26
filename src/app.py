from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio
from src.utils.helpers import (
    generate_http_error_response,
    generate_http_success_response,
)
from src.utils.exceptions import CustomBaseException
from src.utils.logger import get_logger

logger = get_logger()

app = FastAPI(
    title="Box Office",
    description="APIs for event booking",
    version="1.0.1",
)


# In-memory stores
events: Dict[str, dict] = {}
holds: Dict[str, dict] = {}
bookings: Dict[str, dict] = {}

metrics = {
    "total_events": 0,
    "active_holds": 0,
    "bookings": 0,
    "expired_holds": 0,
}
lock = asyncio.Lock()


# --------- Models ---------
class EventCreate(BaseModel):
    name: str
    total_seats: int


class HoldRequest(BaseModel):
    event_id: str
    qty: int


class BookingRequest(BaseModel):
    hold_id: str
    payment_token: str


# --------- Helpers ---------


async def cleanup_event_expired_holds(event: dict):
    """Release seats from expired holds."""
    now = datetime.now()
    expired_holds = [
        h for h in holds.values() if h["expires_at"] < now and h["status"] == "active"
    ]
    for h in expired_holds:
        event["available"] += h["qty"]
        event["held"] -= h["qty"]
        holds[h["status"]]["expired"]
        metrics["expired_holds"] += 1
        metrics["active_holds"] -= 1


async def expire_holds_worker(interval: int = 1):
    """
    Periodically scans and expires holds that are past their TTL.
    Runs every `interval` seconds.
    """
    while True:
        await asyncio.sleep(interval)
        now = datetime.now()

        async with lock:
            expired = []
            for hold_id, hold in holds.items():
                if hold["status"] == "active" and now > hold["expires_at"]:
                    hold["status"] = "expired"
                    event = events.get(hold["event_id"])
                    if event:
                        event["available"] += hold["qty"]
                        event["held"] -= hold["qty"]
                    expired.append(hold_id)
                    metrics["expired_holds"] += 1
                    metrics["active_holds"] -= 1

            if expired:
                logger.info(f"[Worker] Expired holds released: {expired}")


@app.on_event("startup")
async def start_expiry_worker():
    asyncio.create_task(expire_holds_worker())


# --------- API Endpoints ---------


@app.get("/")
async def home():
    return generate_http_success_response(detail="Hello!")


@app.get("/health")
async def health():
    return generate_http_success_response()


@app.get("/metrics")
async def get_metrics():
    return generate_http_success_response(data=metrics)


@app.post("/events")
async def create_event(req: EventCreate):
    try:
        event_id = str(uuid4())
        event = {
            "event_id": event_id,
            "name": req.name,
            "total_seats": req.total_seats,
            "available": req.total_seats,
            "held": 0,
            "booked": 0,
            "created_at": datetime.now(),
        }
        logger.info(f"Event created with event-id: {event_id}")

        events[event_id] = event
        metrics["total_events"] += 1
        resp = {
            "event_id": event_id,
            "total_seats": req.total_seats,
            "created_at": event["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
        }

        return generate_http_success_response(200, data=resp)
    except CustomBaseException as exc:
        return generate_http_error_response(status_code=exc.code, detail=exc.message)
    except Exception as e:
        logger.error("Something has failed", exc_info=e)
        return generate_http_error_response(
            status_code=500, detail="Something has failed. please contact support team"
        )


@app.get("/events/{event_id}")
async def get_event(event_id: str):
    event = events.get(event_id)
    if not event:
        return generate_http_error_response(404, "Event not found")

    resp = {
        "total": event["total_seats"],
        "available": event["available"],
        "held": event["held"],
        "booked": event["booked"],
    }
    return generate_http_success_response(200, data=resp)


@app.post("/holds")
async def create_hold(req: HoldRequest, hold_ttl: int = 2, allot_partial: bool = False):
    event = events.get(req.event_id)
    if not event:
        return generate_http_error_response(404, "Event not found")

    try:
        async with lock:
            # Cleanup expired holds before checking availability
            await cleanup_event_expired_holds(event)

            if req.qty > event["available"]:
                return generate_http_error_response(400, "Not enough seats available")

            # Create hold
            hold_id = str(uuid4())
            payment_token = str(uuid4())
            expires_at = datetime.now() + timedelta(minutes=hold_ttl)

            hold = {
                "hold_id": hold_id,
                "event_id": req.event_id,
                "qty": req.qty,
                "expires_at": expires_at,
                "payment_token": payment_token,
                "status": "active",
            }
            holds[hold_id] = hold
            metrics["active_holds"] += 1

            # Update event state
            event["available"] -= req.qty
            event["held"] += req.qty
            logger.info(
                f"Holding created with event-id: {req.event_id}, hold-id: {hold_id}"
            )

        resp = {
            "hold_id": hold_id,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_token": payment_token,
        }
        return generate_http_success_response(200, data=resp)
    except CustomBaseException as exc:
        return generate_http_error_response(status_code=exc.code, detail=exc.message)
    except Exception as e:
        logger.error("Something has failed", exc_info=e)
        return generate_http_error_response(
            status_code=500, detail="Something has failed. please contact support team"
        )


@app.post("/book")
async def confirm_booking(req: BookingRequest):
    hold = holds.get(req.hold_id)
    if not hold:
        return generate_http_error_response(404, "Hold not found")

    if hold.get("payment_token") != req.payment_token:
        return generate_http_error_response(400, "Invalid payment token")

    if hold.get("expires_at") < datetime.now():
        return generate_http_error_response(400, "Hold expired")

    try:
        # Idempotency: if already booked, return same booking_id
        for b in bookings.values():
            if b["hold_id"] == req.hold_id:
                return generate_http_success_response(
                    200, data={"booking_id": booking_id}
                )

        async with lock:
            event = events[hold["event_id"]]

            if hold["status"] == "success":
                # Already confirmed, return booking_id
                booking_id = [
                    k for k, v in bookings.items() if v["hold_id"] == req.hold_id
                ][0]
                return {"booking_id": booking_id}

            # Confirm booking
            booking_id = str(uuid4())
            bookings[booking_id] = {
                "booking_id": booking_id,
                "event_id": hold["event_id"],
                "hold_id": req.hold_id,
                "qty": hold["qty"],
            }
            logger.info(f"Booking created with booking-id: {booking_id}")

            event["held"] -= hold["qty"]
            event["booked"] += hold["qty"]
            hold["status"] = "success"
            metrics["bookings"] += 1
            metrics["active_holds"] -= 1

        return generate_http_success_response(200, data={"booking_id": booking_id})
    except CustomBaseException as exc:
        return generate_http_error_response(status_code=exc.code, detail=exc.message)
    except Exception as e:
        logger.error("Something has failed", exc_info=e)
        return generate_http_error_response(
            status_code=500, detail="Something has failed. please contact support team"
        )


"""
events[event_id] = {
    "event_id": event_id,
    "name": req.name,
    "total_seats": req.total_seats,
    "available": req.total_seats,
    "held": 0,
    "booked": 0,
    "created_at": datetime.now(),
}

holds[hold_id] = {
    "hold_id": hold_id,
    "event_id": req.event_id,
    "qty": req.qty,
    "expires_at": expires_at,
    "payment_token": payment_token,
    "status": "active",
}

bookings[booking_id] = {
    "booking_id": booking_id,
    "event_id": hold["event_id"],
    "hold_id": req.hold_id,
    "qty": hold["qty"],
}
"""
