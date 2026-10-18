import time
import uuid
import json
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

EMAIL = "your_email@example.com"   # <-- CHANGE THIS to your real email
START_TIME = time.time()

app = FastAPI()

REQUESTS = Counter("http_requests_total", "Total HTTP requests")
LOGS = deque(maxlen=1000)


@app.middleware("http")
async def count_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    REQUESTS.inc()

    response = await call_next(request)

    entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id,
        "method": request.method,
        "status": response.status_code,
    }
    LOGS.append(entry)
    print(json.dumps(entry), flush=True)
    return response


@app.get("/work")
def work(n: int = 1):
    total = 0
    for _ in range(min(max(n, 0), 100000)):
        total += sum(range(1000))
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": float(time.time() - START_TIME)}


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    if limit <= 0:
        return []
    return list(LOGS)[-limit:]