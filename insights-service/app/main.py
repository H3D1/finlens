import os
import httpx
from fastapi import FastAPI, HTTPException
from typing import Optional

from .models import AccountWithTransactions
from .insights import (
    detect_spending_increase,
    detect_recurring_subscriptions,
    project_balance,
)

app = FastAPI(title="Finlens Insights Service")

AGGREGATION_SERVICE_URL = os.getenv(
    "AGGREGATION_SERVICE_URL",
    "http://localhost:8080",
)


@app.get("/insights/{user_id}")
async def get_insights(user_id: int, authorization: str | None = None):
    """
    Fetch accounts and transactions for the given user from the aggregation
    service, compute spending alerts, recurring subscriptions, and a balance
    projection, then return a structured JSON response.
    """
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{AGGREGATION_SERVICE_URL}/accounts",
            headers=headers,
        )

    if resp.is_error:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Aggregation service returned {resp.status_code}: {resp.text}",
        )

    raw = resp.json()

    # Parse the response into our models
    try:
        accounts = [AccountWithTransactions(**item) for item in raw]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse aggregation response: {exc}",
        )

    spending_alerts = detect_spending_increase(accounts)
    subscriptions = detect_recurring_subscriptions(accounts)
    balance_projection = project_balance(accounts)

    return {
        "spending_alerts": spending_alerts,
        "subscriptions": subscriptions,
        "balance_projection": balance_projection,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}