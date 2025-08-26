# 🎟️ Jangam Sravan's Box Office

A minimal FastAPI-based ticket booking system that supports:
- Event creation with total seats
- Temporary seat holds with TTL
- Booking confirmation with idempotency
- Partial fulfillment policy
- Metrics on events, holds, bookings, and expiries (optional bonus)

![Architecture](./architecture.png)
---

## 📦 Key Modules

### 1. **API Endpoints**
- `POST /events` → Create an event (`name`, `total_seats`)
- `POST /holds` → Request temporary seat hold (`event_id`, `qty`, `ttl`)
- `POST /book` → Confirm booking with an active hold (`hold_id`, `payment_token`)
- `GET /events/{id}` → Get snapshot of event state (`total`, `available`, `held`, `booked`)
- `GET /metrics` → Monitoring endpoint: totals, active holds, bookings, expiries

### 2. **Concurrency Control**
- Uses **`asyncio.Lock`** (for async FastAPI) to prevent oversubscription when multiple concurrent hold/booking requests occur.
- Critical sections:
  - ticket availability check
  - Hold creation
  - Booking confirmation

### 3. **Background Worker**
- A **background task** runs every few seconds to:
  - Scan active holds
  - Expire holds past their `expires_at`
  - Return seats back to `available`

### 4. **Idempotency**
- Each booking request requires `{hold_id, payment_token}`.
- Bookings are idempotent:
  - If retried with same `hold_id` and `payment_token`, it returns the same `booking_id`.
  - Prevents double-booking due to network retries.

---


## 🗄️ Data Model

In-memory Python dicts (can be swapped with DB later):

```python
events = {
  event_id: {
    "name": str,
    "total_seats": int,
    "available": int,
    "held": int,
    "booked": int,
    "created_at": datetime
  }
}

holds = {
  hold_id: {
    "event_id": str,
    "qty": int,
    "expires_at": datetime,
    "payment_token": str,
    "status": "active" | "expired" | "booked"
  }
}

bookings = {
  booking_id: {
    "event_id": str,
    "hold_id": str,
    "qty": int,
    "created_at": datetime
  }
}

```

---


## 🚀 How to Run

Note: Docker need to be installed.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ticket-booking-system.git
cd ticket-booking-system
```
### 2. Build & Launch with Docker
```
chmod +x launch.sh
./launch.sh
```
---

## 🚀 Sample Use
### Create event
```
- curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"name": "Concert", "total_seats": 100}'
```

### Hold seats
```
- curl -X POST http://localhost:8000/holds \
  -H "Content-Type: application/json" \
  -d '{"event_id": "1", "qty": 5}'
```

### Confirm booking
```
- curl -X POST http://localhost:8000/book \
  -H "Content-Type: application/json" \
  -d '{"hold_id": "abc123", "payment_token": "xyz789"}'
```
