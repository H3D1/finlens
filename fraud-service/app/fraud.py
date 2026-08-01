from datetime import datetime, timedelta, timezone
from collections import defaultdict
from decimal import Decimal
from typing import Optional

from .models import AccountWithTransactions, Transaction


def check_velocity(
    accounts: list[AccountWithTransactions],
    *,
    max_transactions: int = 5,
    window_minutes: int = 10,
) -> list[dict]:
    """
    Velocity check: detect bursts of outgoing transactions from the same
    account that exceed max_transactions within a rolling window of
    window_minutes minutes.

    Returns a list of alerts, each containing:
      - account_id
      - transaction_count: number of transactions in the window
      - window_minutes
      - total_amount: sum of the amounts in that window
      - earliest / latest timestamps in the window
    """
    alerts: list[dict] = []
    now = datetime.now(timezone.utc)

    for acc_wtx in accounts:
        acc_id = acc_wtx.account.id
        # Only outgoing (negative) transactions — debits / spending
        outgoing = sorted(
            [t for t in acc_wtx.transactions if t.amount < 0],
            key=lambda t: t.timestamp,
        )

        if len(outgoing) < max_transactions:
            continue

        # Sliding window check
        for i in range(len(outgoing) - max_transactions + 1):
            window = outgoing[i : i + max_transactions]
            start = window[0].timestamp
            end = window[-1].timestamp
            span = (end - start).total_seconds() / 60  # minutes

            if span <= window_minutes:
                total = sum(t.amount for t in window)
                alerts.append({
                    "account_id": acc_id,
                    "transaction_count": max_transactions,
                    "window_minutes": window_minutes,
                    "actual_span_minutes": round(span, 2),
                    "total_amount": float(abs(total)),
                    "earliest": start.isoformat(),
                    "latest": end.isoformat(),
                    "transaction_ids": [t.id for t in window],
                })
                # Move past this window to avoid a cluster of overlapping alerts
                # by skipping ahead to the next transaction after this window
                # (simple approach: break after first match per account to
                # avoid flooding, or continue checking all windows)
                break

    return alerts