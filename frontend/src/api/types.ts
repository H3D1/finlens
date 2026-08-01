export interface Transaction {
  id: number;
  accountId: number;
  amount: number;
  description: string;
  timestamp: string;
  category: string;
}

export interface Account {
  id: number;
  userId: number;
  type: 'CHECKING' | 'SAVINGS' | 'CREDIT_CARD';
  balance: number;
  currency: string;
}

export interface AccountWithTransactions {
  account: Account;
  transactions: Transaction[];
}

export interface SpendingAlert {
  category: string;
  current_month_total: number;
  prior_average: number;
  increase_percent: number;
}

export interface Subscription {
  description: string;
  amount: number;
  occurrences: number;
}

export interface BalanceProjection {
  average_daily_net_change: number;
  projected_days_until_zero: number;
  current_balance: number;
}

export interface InsightsResponse {
  spending_alerts: SpendingAlert[];
  subscriptions: Subscription[];
  balance_projection: BalanceProjection | null;
}

export interface FraudFlag {
  transaction_id: number;
  account_id: number;
  amount: number;
  description: string;
  category: string;
  timestamp: string;
  reason: string;
  reason_detail: string;
}

export interface FraudResponse {
  flags: FraudFlag[];
}