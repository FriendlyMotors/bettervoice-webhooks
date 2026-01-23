#!/usr/bin/env python3
import os
import json
import logging
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "bettervoice-webhook"
APP_VERSION = "0.1.0"

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger(APP_NAME)
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%dT%H:%M:%S%z"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


app = FastAPI(title=APP_NAME, version=APP_VERSION)

# CORS - allow all origins for now (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to explicit origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/webhook")
async def receive_webhook(request: Request) -> JSONResponse:
    """
    Receive BetterVoice webhook events.

    - Attempts to parse JSON body; if parsing fails it will log raw body.
    - Logs headers, client IP, and the parsed payload (or raw body).
    - Returns a simple 200 OK JSON response.
    """
    client_ip: Optional[str] = None
    if request.client:
        client_ip = request.client.host

    headers = {k: v for k, v in request.headers.items()}

    body: Any = None
    body_type = "unknown"
    try:
        body = await request.json()
        body_type = "json"
    except Exception:
        # Fallback: read raw body and attempt to decode
        raw = await request.body()
        try:
            body = raw.decode("utf-8")
            body_type = "text"
        except Exception:
            body = raw
            body_type = "bytes"

    # Safe serialization for logging
    try:
        serialized_body = json.dumps(body, ensure_ascii=False, default=str)
    except Exception:
        serialized_body = str(body)

    logger.info(
        "Received webhook event",
        extra={
            "source": "bettervoice",
            "client_ip": client_ip,
            "headers": headers,
            "body_type": body_type,
            "body": serialized_body,
        },
    )

    # Placeholder: add verification and business logic here

    return JSONResponse({"received": True, "status": "ok"})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )