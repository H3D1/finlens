import type {
  AccountWithTransactions,
  InsightsResponse,
  FraudResponse,
} from './types';

const AGGREGATION_BASE = '/api';
const INSIGHTS_BASE = '/insights';
const FRAUD_BASE = '/fraud';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(url: string, token: string | null): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url, { headers });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = (body as { detail?: string; message?: string }).detail
        ?? (body as { message?: string }).message
        ?? detail;
    } catch { /* fall back to default message */ }
    throw new ApiError(detail, res.status);
  }

  return res.json() as Promise<T>;
}

export function getAccounts(token: string): Promise<AccountWithTransactions[]> {
  return request<AccountWithTransactions[]>(`${AGGREGATION_BASE}/accounts`, token);
}

export function getInsights(userId: number, token: string): Promise<InsightsResponse> {
  return request<InsightsResponse>(`${INSIGHTS_BASE}/${userId}`, token);
}

export function getFraudFlags(userId: number, token: string): Promise<FraudResponse> {
  return request<FraudResponse>(`${FRAUD_BASE}/flags/${userId}`, token);
}