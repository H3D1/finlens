from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class Transaction(BaseModel):
    id: int
    accountId: int
    amount: Decimal
    description: str
    timestamp: datetime
    category: str


class Account(BaseModel):
    id: int
    userId: int
    type: str
    balance: Decimal
    currency: str


class AccountWithTransactions(BaseModel):
    account: Account
    transactions: list[Transaction]