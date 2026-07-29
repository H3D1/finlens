import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

from app.models import Account, Transaction, AccountWithTransactions
from app.insights import (
    detect_spending_increase,
    detect_recurring_subscriptions,
    project_balance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_account(
    id: int = 1,
    user_id: int = 1,
    balance: Decimal = Decimal("1000"),
) -> Account:
    return Account(id=id, userId=user_id, type="CHECKING", balance=balance, currency="USD")


def make_tx(
    *,
    id: int = 1,
    account_id: int = 1,
    amount: Decimal = Decimal("-50"),
    description: str = "coffee",
    timestamp: datetime | None = None,
    category: str = "Food",
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


# We'll freeze time to mid-July 2026 so that:
#   current month   = July 2026
#   prior 2 months  = June 2026, May 2026
FROZEN_NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


# ===================================================================
# detect_spending_increase
# ===================================================================

class TestDetectSpendingIncrease:

    @patch("app.insights.datetime")
    def test_triggers_on_25_percent_increase(self, mock_dt):
        """Current month total is 50% higher than prior 2-month average -> alert."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        # Current month: July 2026
        t_jul = make_tx(id=1, amount=Decimal("-150"), timestamp=FROZEN_NOW, category="Food")
        # Prior month June 2026
        t_jun = make_tx(id=2, amount=Decimal("-100"), timestamp=datetime(2026, 6, 10, tzinfo=timezone.utc), category="Food")
        # Prior month May 2026
        t_may = make_tx(id=3, amount=Decimal("-100"), timestamp=datetime(2026, 5, 5, tzinfo=timezone.utc), category="Food")

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t_jul, t_jun, t_may])

        alerts = detect_spending_increase([awt])
        assert len(alerts) == 1
        assert alerts[0]["category"] == "Food"
        assert alerts[0]["increase_percent"] >= 25

    @patch("app.insights.datetime")
    def test_no_alert_when_increase_is_below_25_percent(self, mock_dt):
        """Current month total is only 10% higher -> no alert."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        # Current: 110
        t_jul = make_tx(id=1, amount=Decimal("-110"), timestamp=FROZEN_NOW, category="Food")
        # Prior: avg 100
        t_jun = make_tx(id=2, amount=Decimal("-100"), timestamp=datetime(2026, 6, 10, tzinfo=timezone.utc), category="Food")
        t_may = make_tx(id=3, amount=Decimal("-100"), timestamp=datetime(2026, 5, 5, tzinfo=timezone.utc), category="Food")

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t_jul, t_jun, t_may])

        alerts = detect_spending_increase([awt])
        assert alerts == []

    @patch("app.insights.datetime")
    def test_no_alert_when_no_prior_data(self, mock_dt):
        """Only current month transactions exist -> can't compare -> no alert."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        t_jul = make_tx(id=1, amount=Decimal("-200"), timestamp=FROZEN_NOW, category="Food")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t_jul])

        alerts = detect_spending_increase([awt])
        assert alerts == []

    @patch("app.insights.datetime")
    def test_no_alert_when_prior_average_is_zero(self, mock_dt):
        """Prior average is 0 -> division by zero avoided -> no alert."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        # Current: 50, but prior months have 0 in this category (no transactions)
        t_jul = make_tx(id=1, amount=Decimal("-50"), timestamp=FROZEN_NOW, category="Entertainment")
        # Only other-category transactions in prior months
        t_jun = make_tx(id=2, amount=Decimal("-100"), timestamp=datetime(2026, 6, 10, tzinfo=timezone.utc), category="Food")

        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t_jul, t_jun])

        alerts = detect_spending_increase([awt])
        # 'Entertainment' only appears in current month -> no alert
        entertainment_alerts = [a for a in alerts if a["category"] == "Entertainment"]
        assert entertainment_alerts == []


# ===================================================================
# detect_recurring_subscriptions
# ===================================================================

class TestDetectRecurringSubscriptions:

    def test_detects_subscription_with_30_day_gap(self):
        """Two identical charges 30 days apart -> flagged."""
        now = datetime(2026, 7, 15, tzinfo=timezone.utc)
        t1 = make_tx(id=1, amount=Decimal("-15.99"), description="Netflix",
                     timestamp=now, category="Subscription")
        t2 = make_tx(id=2, amount=Decimal("-15.99"), description="Netflix",
                     timestamp=now - timedelta(days=30), category="Subscription")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t1, t2])

        subs = detect_recurring_subscriptions([awt])
        assert len(subs) == 1
        assert subs[0]["description"] == "netflix"
        assert subs[0]["amount"] == 15.99

    def test_no_subscription_when_gap_too_large(self):
        """Two identical charges but gap is 40 days -> not flagged."""
        now = datetime(2026, 7, 20, tzinfo=timezone.utc)
        t1 = make_tx(id=1, amount=Decimal("-9.99"), description="Spotify",
                     timestamp=now, category="Subscription")
        t2 = make_tx(id=2, amount=Decimal("-9.99"), description="Spotify",
                     timestamp=now - timedelta(days=40), category="Subscription")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t1, t2])

        subs = detect_recurring_subscriptions([awt])
        assert subs == []

    def test_no_subscription_when_gap_too_small(self):
        """Two identical charges but gap is 10 days -> not flagged."""
        now = datetime(2026, 7, 20, tzinfo=timezone.utc)
        t1 = make_tx(id=1, amount=Decimal("-9.99"), description="Spotify",
                     timestamp=now, category="Subscription")
        t2 = make_tx(id=2, amount=Decimal("-9.99"), description="Spotify",
                     timestamp=now - timedelta(days=10), category="Subscription")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t1, t2])

        subs = detect_recurring_subscriptions([awt])
        assert subs == []

    def test_ignores_positive_amounts(self):
        """Positive (income) transactions are ignored."""
        now = datetime(2026, 7, 20, tzinfo=timezone.utc)
        t1 = make_tx(id=1, amount=Decimal("2000"), description="Salary",
                     timestamp=now, category="Income")
        t2 = make_tx(id=2, amount=Decimal("2000"), description="Salary",
                     timestamp=now - timedelta(days=30), category="Income")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t1, t2])

        subs = detect_recurring_subscriptions([awt])
        assert subs == []

    def test_single_occurrence_no_subscription(self):
        """Only one transaction -> not enough for a subscription."""
        now = datetime(2026, 7, 20, tzinfo=timezone.utc)
        t1 = make_tx(id=1, amount=Decimal("-5.00"), description="Newsletter",
                     timestamp=now, category="Subscription")
        acc = make_account()
        awt = AccountWithTransactions(account=acc, transactions=[t1])

        subs = detect_recurring_subscriptions([awt])
        assert subs == []


# ===================================================================
# project_balance
# ===================================================================

class TestProjectBalance:

    @patch("app.insights.datetime")
    def test_projects_days_until_zero_when_spending(self, mock_dt):
        """Net negative over 14 days -> returns projection."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        cutoff = FROZEN_NOW - timedelta(days=14)

        # Create 14 daily outgoing transactions of -10 each -> daily_rate = -10
        txs = []
        for day in range(14):
            t = make_tx(
                id=day + 1,
                amount=Decimal("-10"),
                description="daily spend",
                timestamp=cutoff + timedelta(days=day, hours=12),
                category="Misc",
            )
            txs.append(t)

        acc = make_account(balance=Decimal("500"))
        awt = AccountWithTransactions(account=acc, transactions=txs)

        proj = project_balance([awt])
        assert proj is not None
        assert proj["average_daily_net_change"] == pytest.approx(-10, abs=0.1)
        # 500 / 10 = 50 days
        assert proj["projected_days_until_zero"] == pytest.approx(50, abs=1)
        assert proj["current_balance"] == 500.0

    @patch("app.insights.datetime")
    def test_returns_none_when_trend_is_flat(self, mock_dt):
        """No net change over 14 days -> no projection."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        cutoff = FROZEN_NOW - timedelta(days=14)

        # Equal spend and income -> net zero
        txs = [
            make_tx(id=1, amount=Decimal("-100"), description="spend",
                    timestamp=cutoff + timedelta(days=1), category="Food"),
            make_tx(id=2, amount=Decimal("100"), description="refund",
                    timestamp=cutoff + timedelta(days=1), category="Income"),
        ]
        acc = make_account(balance=Decimal("500"))
        awt = AccountWithTransactions(account=acc, transactions=txs)

        proj = project_balance([awt])
        assert proj is None

    @patch("app.insights.datetime")
    def test_returns_none_when_trend_is_positive(self, mock_dt):
        """Net positive over 14 days (saving) -> no projection."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        cutoff = FROZEN_NOW - timedelta(days=14)

        txs = [
            make_tx(id=1, amount=Decimal("200"), description="income",
                    timestamp=cutoff + timedelta(days=1), category="Income"),
            make_tx(id=2, amount=Decimal("-50"), description="spend",
                    timestamp=cutoff + timedelta(days=1), category="Food"),
        ]
        acc = make_account(balance=Decimal("500"))
        awt = AccountWithTransactions(account=acc, transactions=txs)

        proj = project_balance([awt])
        assert proj is None

    @patch("app.insights.datetime")
    def test_returns_none_when_no_recent_transactions(self, mock_dt):
        """No transactions in last 14 days -> no projection."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        old = make_tx(
            id=1, amount=Decimal("-100"), description="old",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            category="Food",
        )
        acc = make_account(balance=Decimal("500"))
        awt = AccountWithTransactions(account=acc, transactions=[old])

        proj = project_balance([awt])
        assert proj is None

    @patch("app.insights.datetime")
    def test_aggregates_multiple_accounts(self, mock_dt):
        """Transactions from multiple accounts are summed together."""
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw) if a else FROZEN_NOW

        cutoff = FROZEN_NOW - timedelta(days=14)

        # Account 1: 14 days of -5  -> -70 total
        txs1 = []
        for day in range(14):
            t = make_tx(id=day + 1, account_id=1, amount=Decimal("-5"),
                        timestamp=cutoff + timedelta(days=day, hours=12),
                        category="Misc")
            txs1.append(t)

        # Account 2: 14 days of -3  -> -42 total
        txs2 = []
        for day in range(14):
            t = make_tx(id=20 + day, account_id=2, amount=Decimal("-3"),
                        timestamp=cutoff + timedelta(days=day, hours=12),
                        category="Misc")
            txs2.append(t)

        acc1 = make_account(id=1, balance=Decimal("200"))
        acc2 = make_account(id=2, balance=Decimal("100"))

        awt1 = AccountWithTransactions(account=acc1, transactions=txs1)
        awt2 = AccountWithTransactions(account=acc2, transactions=txs2)

        proj = project_balance([awt1, awt2])
        assert proj is not None
        # total net = -112 over 14 days -> daily_rate = -8
        assert proj["average_daily_net_change"] == pytest.approx(-8, abs=0.5)
        # total balance = 300 / 8 = 37.5 days
        assert proj["projected_days_until_zero"] == pytest.approx(37.5, abs=1)
        assert proj["current_balance"] == pytest.approx(300.0)
