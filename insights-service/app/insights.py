from datetime import datetime, timedelta, timezone
from decimal import Decimal
from collections import defaultdict
from typing import Optional

from .models import AccountWithTransactions, Transaction


def detect_spending_increase(
    accounts: list[AccountWithTransactions],
) -> list[dict]:
    """
    Group transactions by category, compare the current calendar month's total
    per category to the average of the prior 2 months for that same category.
    Flag any category where the increase is 25% or more.
    """
    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month

    # Determine month boundaries
    def month_range(year: int, month: int):
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        return start, next_month

    cur_start, cur_end = month_range(current_year, current_month)

    # Prior 2 months
    prior_months = []
    for i in (1, 2):
        m = current_month - i
        y = current_year
        if m <= 0:
            m += 12
            y -= 1
        prior_months.append(month_range(y, m))

    # Collect transactions
    def all_transactions() -> list[Transaction]:
        for acc in accounts:
            yield from acc.transactions

    # Aggregate by category
    current_totals: dict[str, Decimal] = defaultdict(Decimal)
    prior_totals: dict[str, list[Decimal]] = defaultdict(list)

    for t in all_transactions():
        if cur_start <= t.timestamp < cur_end:
            current_totals[t.category] += t.amount
        for pm_start, pm_end in prior_months:
            if pm_start <= t.timestamp < pm_end:
                prior_totals[t.category].append(t.amount)

    alerts: list[dict] = []
    for category, cur_total in current_totals.items():
        amounts = prior_totals.get(category, [])
        if not amounts:
            continue
        # Average of prior 2 months (sum / number of months with data)
        # We group by month, so we need the sum per month
        prior_by_month: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
        for pm_start, pm_end in prior_months:
            for t in all_transactions():
                if t.category == category and pm_start <= t.timestamp < pm_end:
                    prior_by_month[(pm_start.year, pm_start.month)] += t.amount

        if not prior_by_month:
            continue

        avg_prior = sum(prior_by_month.values(), Decimal(0)) / len(prior_by_month)

        if avg_prior == 0:
            continue

        increase_pct = (cur_total - avg_prior) / avg_prior * 100

        if increase_pct >= Decimal("25"):
            alerts.append({
                "category": category,
                "current_month_total": float(cur_total),
                "prior_average": float(avg_prior),
                "increase_percent": float(round(increase_pct, 2)),
            })

    return alerts


def detect_recurring_subscriptions(
    accounts: list[AccountWithTransactions],
) -> list[dict]:
    """
    Group transactions by exact same amount AND exact same description.
    Flag as a recurring subscription if at least 2 occurrences exist with a
    gap of 25-35 days between them.
    """
    # Collect all negative-amount transactions (subscriptions are outgoing)
    outgoing: list[Transaction] = []
    for acc in accounts:
        for t in acc.transactions:
            if t.amount < 0:
                outgoing.append(t)

    # Group by (description, amount)
    groups: dict[tuple[str, float], list[datetime]] = defaultdict(list)
    for t in outgoing:
        key = (t.description.strip().lower(), float(t.amount))
        groups[key].append(t.timestamp)

    subscriptions: list[dict] = []
    for (desc, amt), timestamps in groups.items():
        if len(timestamps) < 2:
            continue
        timestamps.sort()
        # Check if any pair has a gap of 25-35 days
        found = False
        for i in range(len(timestamps) - 1):
            gap = (timestamps[i + 1] - timestamps[i]).days
            if 25 <= gap <= 35:
                found = True
                break
        if found:
            subscriptions.append({
                "description": desc,
                "amount": abs(amt),
                "occurrences": len(timestamps),
            })

    return subscriptions


def project_balance(
    accounts: list[AccountWithTransactions],
) -> Optional[dict]:
    """
    Calculate the average daily net change (income minus spending) over the
    last 14 days. Project the number of days until the account balance reaches
    zero at that rate, or return None if the trend is flat or increasing.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=14)

    # Sum all transactions across all accounts in the last 14 days
    all_transactions: list[Transaction] = []
    for acc in accounts:
        all_transactions.extend(acc.transactions)

    recent = [t for t in all_transactions if t.timestamp >= cutoff]

    if not recent:
        return None

    total_net = sum(t.amount for t in recent)
    daily_rate = total_net / Decimal("14")

    # If flat or positive (increasing balance), no projection
    if daily_rate >= 0:
        return None

    # Total current balance across all accounts
    total_balance = sum(acc.account.balance for acc in accounts)

    # Days until zero: balance / abs(daily_rate)
    days_until_zero = abs(total_balance / daily_rate)

    return {
        "average_daily_net_change": float(round(daily_rate, 2)),
        "projected_days_until_zero": float(round(days_until_zero, 1)),
        "current_balance": float(total_balance),
    }