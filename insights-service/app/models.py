from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class Account(BaseModel):
    id: int
    userId: int
    type: str  # CHECKING, SAVINGS, CREDIT_CARD
    balance: Decimal
    currency: str


class Transaction(BaseModel):
    id: int
    accountId: int
    amount: Decimal
    description: str
    timestamp: datetime
    category: str


class AccountWithTransactions(BaseModel):
    account: Account
    transactions: list[Transaction]