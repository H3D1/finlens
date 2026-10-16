import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header

from .models import AccountWithTransactions
from .fraud import check_velocity

app = FastAPI(title="Finlens Fraud Service")

AGGREGATION_SERVICE_URL = os.getenv(
    "AGGREGATION_SERVICE_URL",
    "http://localhost:8080",
)


@app.get("/fraud/flags/{user_id}")
async def get_fraud_flags(
    user_id: int,
    authorization: str | None = Header(default=None),
):
    """
    Fetch the user's accounts/transactions from the aggregation service,
    run the velocity check, and return flagged transactions with a reason.
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

    try:
        accounts = [AccountWithTransactions(**item) for item in raw]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse aggregation response: {exc}",
        )

    alerts = check_velocity(accounts)

    # Build a list of flagged transaction objects
    flagged_transactions = []
    for alert in alerts:
        for acc_wtx in accounts:
            if acc_wtx.account.id != alert["account_id"]:
                continue
            for txn in acc_wtx.transactions:
                if txn.id in alert["transaction_ids"]:
                    flagged_transactions.append({
                        "transaction_id": txn.id,
                        "account_id": txn.accountId,
                        "amount": float(txn.amount),
                        "description": txn.description,
                        "category": txn.category,
                        "timestamp": txn.timestamp.isoformat(),
                        "reason": "velocity",
                        "reason_detail": (
                            f"{alert['transaction_count']} transactions in "
                            f"{alert['actual_span_minutes']} minutes"
                        ),
                    })

    return {"flags": flagged_transactions}


@app.get("/health")
async def health():
    return {"status": "ok"}
