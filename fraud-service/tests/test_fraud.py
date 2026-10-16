import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import Account, Transaction, AccountWithTransactions
from app.fraud import check_velocity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_account(
    id: int = 1,
    user_id: int = 1,
    balance: Decimal = Decimal("5000"),
) -> Account:
    return Account(id=id, userId=user_id, type="CHECKING", balance=balance, currency="USD")


def make_tx(
    *,
    id: int = 1,
    account_id: int = 1,
    amount: Decimal = Decimal("-100"),
    description: str = "payment",
    timestamp: datetime | None = None,
    category: str = "Transfer",
) -> Transaction:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return Transaction(
        id=id,
        accountId=account_id,
        amount=amount,
        description=description,
        timestamp=timestamp,
        category=category,
    )


BASE_TIME = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


# ===================================================================
# check_velocity
# ===================================================================

class TestCheckVelocity:

    def test_triggers_alert_on_5_tx_in_10_minutes(self):
        """Five outgoing transactions within a 10-minute window -> flagged."""
        txs = []
        for i in range(5):
            t = make_tx(
                id=i + 1,
                amount=Decimal("-200"),
                description=f"tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 2),  # spans 0-8 min
                category="Transfer",
            )
            txs.append(t)

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=txs)

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert len(alerts) == 1
        assert alerts[0]["account_id"] == 1
        assert alerts[0]["transaction_count"] == 5
        assert alerts[0]["window_minutes"] == 10
        assert alerts[0]["actual_span_minutes"] <= 10
        assert alerts[0]["rule_id"] == "transaction_velocity"
        assert alerts[0]["reason"] == (
            "5 outgoing transactions detected within 10 minutes."
        )
        assert alerts[0]["threshold"] == {
            "transaction_count": 5,
            "window_minutes": 10,
        }
        assert alerts[0]["transaction_ids"] == [1, 2, 3, 4, 5]

    def test_no_alert_when_tx_spread_over_30_minutes(self):
        """Five outgoing transactions spread over 30 minutes -> no alert."""
        txs = []
        for i in range(5):
            t = make_tx(
                id=i + 1,
                amount=Decimal("-100"),
                description=f"tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 8),  # spans 0-32 min
                category="Transfer",
            )
            txs.append(t)

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=txs)

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert alerts == []

    def test_no_alert_with_fewer_than_max_transactions(self):
        """Only 4 transactions in 10 minutes -> not enough to trigger."""
        txs = []
        for i in range(4):
            t = make_tx(
                id=i + 1,
                amount=Decimal("-50"),
                description=f"tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 2),  # spans 0-6 min
                category="Transfer",
            )
            txs.append(t)

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=txs)

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert alerts == []

    def test_no_alert_with_only_positive_transactions(self):
        """All transactions are income (positive) -> no outgoing -> no alert."""
        txs = []
        for i in range(5):
            t = make_tx(
                id=i + 1,
                amount=Decimal("500"),  # positive = income
                description=f"income {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 2),
                category="Income",
            )
            txs.append(t)

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=txs)

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert alerts == []

    def test_no_alert_with_empty_accounts(self):
        """No transactions at all -> no alert."""
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[])

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert alerts == []

    def test_triggers_with_multiple_accounts_only_flagged_one(self):
        """Two accounts: one triggers velocity, the other does not."""
        # Account 1: triggers (5 tx in 9 min)
        txs1 = []
        for i in range(5):
            t = make_tx(
                id=i + 1,
                account_id=1,
                amount=Decimal("-100"),
                description=f"fast tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 2),
                category="Transfer",
            )
            txs1.append(t)

        # Account 2: no trigger (only 3 tx)
        txs2 = []
        for i in range(3):
            t = make_tx(
                id=10 + i,
                account_id=2,
                amount=Decimal("-50"),
                description=f"slow tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 10),
                category="Transfer",
            )
            txs2.append(t)

        acc1 = make_account(id=1)
        acc2 = make_account(id=2)

        awt1 = AccountWithTransactions(account=acc1, transactions=txs1)
        awt2 = AccountWithTransactions(account=acc2, transactions=txs2)

        alerts = check_velocity([awt1, awt2], max_transactions=5, window_minutes=10)
        assert len(alerts) == 1
        assert alerts[0]["account_id"] == 1

    def test_triggers_exactly_at_boundary(self):
        """Exactly 10 minutes for 5 transactions -> should trigger (<=)."""
        txs = []
        for i in range(5):
            t = make_tx(
                id=i + 1,
                amount=Decimal("-75"),
                description=f"tx {i}",
                timestamp=BASE_TIME + timedelta(minutes=i * 2.5),  # spans 0-10 min exactly
                category="Transfer",
            )
            txs.append(t)

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=txs)

        alerts = check_velocity([awt], max_transactions=5, window_minutes=10)
        assert len(alerts) == 1
        assert alerts[0]["actual_span_minutes"] == 10.0