import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import {
  getAccounts,
  getInsights,
  getFraudFlags,
  ApiError,
} from '../api/client';
import type {
  AccountWithTransactions,
  InsightsResponse,
  FraudFlag,
} from '../api/types';

function formatMoney(value: number, currency = 'USD', sign = true): string {
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(Math.abs(value));
  return sign && value < 0 ? `-${formatted}` : formatted;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function DashboardPage() {
  const { token, userId, email, logout } = useAuth();

  const [accounts, setAccounts] = useState<AccountWithTransactions[] | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [fraudFlags, setFraudFlags] = useState<FraudFlag[] | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || userId === null) return;
    const authToken: string = token;
    const authUserId: number = userId;

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError('');
      try {
        const [accountsData, insightsData, fraudData] = await Promise.all([
          getAccounts(authToken),
          getInsights(authUserId, authToken),
          getFraudFlags(authUserId, authToken),
        ]);
        if (cancelled) return;
        setAccounts(accountsData);
        setInsights(insightsData);
        setFraudFlags(fraudData.flags);
      } catch (err: unknown) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          logout();
          return;
        }
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => { cancelled = true; };
  }, [token, userId, logout]);

  if (loading) {
    return (
      <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 16px' }}>
        <p>Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Dashboard</h1>
        <div>
          <span style={{ marginRight: 12 }}>{email}</span>
          <button onClick={logout} style={{ padding: '6px 16px' }}>
            Sign out
          </button>
        </div>
      </div>
      <hr />

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {/* ───── Section 1: Accounts & Transactions ───── */}
      <section style={{ marginBottom: 32 }}>
        <h2>Accounts</h2>
        {accounts && accounts.length > 0 ? (
          accounts.map(({ account, transactions }) => (
            <div
              key={account.id}
              style={{
                border: '1px solid #ddd',
                borderRadius: 8,
                padding: 16,
                marginBottom: 16,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{account.type.replace('_', ' ')}</strong>
                <span>
                  Balance:{' '}
                  {formatMoney(Number(account.balance), account.currency)}
                </span>
              </div>
              {transactions.length > 0 ? (
                <table style={{ width: '100%', marginTop: 12, borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Date</th>
                      <th style={{ textAlign: 'left' }}>Description</th>
                      <th style={{ textAlign: 'left' }}>Category</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.slice(0, 10).map((tx) => (
                      <tr key={tx.id}>
                        <td style={{ padding: '4px 8px 4px 0' }}>{formatDate(tx.timestamp)}</td>
                        <td style={{ padding: '4px 8px' }}>{tx.description}</td>
                        <td style={{ padding: '4px 8px' }}>{tx.category}</td>
                        <td
                          style={{
                            padding: '4px 0 4px 8px',
                            textAlign: 'right',
                            color: Number(tx.amount) < 0 ? '#c0392b' : '#27ae60',
                          }}
                        >
                          {formatMoney(Number(tx.amount), account.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p style={{ color: '#777', marginTop: 8 }}>No transactions.</p>
              )}
            </div>
          ))
        ) : (
          <p>No accounts found.</p>
        )}
      </section>

      {/* ───── Section 2: Insights ───── */}
      <section style={{ marginBottom: 32 }}>
        <h2>Insights</h2>
        {insights ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ marginBottom: 8 }}>Spending alerts</h3>
              {insights.spending_alerts.length > 0 ? (
                <ul>
                  {insights.spending_alerts.map((alert) => (
                    <li key={alert.category}>
                      <strong>{alert.category}</strong> — {alert.increase_percent}% increase
                      <span style={{ color: '#777' }}>
                        {' '}
                        (now {formatMoney(alert.current_month_total)} vs avg{' '}
                        {formatMoney(alert.prior_average)})
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: '#777' }}>No spending alerts.</p>
              )}
            </div>

            <div style={{ marginBottom: 16 }}>
              <h3 style={{ marginBottom: 8 }}>Subscriptions</h3>
              {insights.subscriptions.length > 0 ? (
                <ul>
                  {insights.subscriptions.map((sub, i) => (
                    <li key={`${sub.description}-${i}`}>
                      <strong>{sub.description}</strong> — {formatMoney(sub.amount)}{' '}
                      <span style={{ color: '#777' }}>· {sub.occurrences} occurrences</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: '#777' }}>No subscriptions detected.</p>
              )}
            </div>

            <div>
              <h3 style={{ marginBottom: 8 }}>Balance projection</h3>
              {insights.balance_projection ? (
                <p>
                  At your current rate of {formatMoney(insights.balance_projection.average_daily_net_change)}/day,
                  your balance of {formatMoney(insights.balance_projection.current_balance)} is projected to
                  reach zero in{' '}
                  <strong>{Math.round(insights.balance_projection.projected_days_until_zero)} days</strong>.
                </p>
              ) : (
                <p style={{ color: '#777' }}>No projection — your balance trend is flat or increasing.</p>
              )}
            </div>
          </>
        ) : (
          <p style={{ color: '#777' }}>Insights unavailable.</p>
        )}
      </section>

      {/* ───── Section 3: Fraud Flags ───── */}
      <section style={{ marginBottom: 32 }}>
        <h2>Fraud flags</h2>
        {fraudFlags ? (
          fraudFlags.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Date</th>
                  <th style={{ textAlign: 'left' }}>Description</th>
                  <th style={{ textAlign: 'left' }}>Reason</th>
                  <th style={{ textAlign: 'right' }}>Amount</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {fraudFlags.map((flag) => (
                  <tr key={flag.transaction_id}>
                    <td style={{ padding: '4px 8px 4px 0' }}>{formatDate(flag.timestamp)}</td>
                    <td style={{ padding: '4px 8px' }}>{flag.description}</td>
                    <td style={{ padding: '4px 8px', color: '#777' }}>{flag.reason_detail}</td>
                    <td style={{ padding: '4px 0 4px 8px', textAlign: 'right' }}>
                      {formatMoney(flag.amount)}
                    </td>
                    <td style={{ padding: '4px 0 4px 8px', textAlign: 'right' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          background: '#e74c3c',
                          color: '#fff',
                          borderRadius: 12,
                          padding: '2px 10px',
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        ⚠ FLAGGED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#777' }}>No suspicious activity detected.</p>
          )
        ) : (
          <p style={{ color: '#777' }}>Fraud check unavailable.</p>
        )}
      </section>
    </div>
  );
}