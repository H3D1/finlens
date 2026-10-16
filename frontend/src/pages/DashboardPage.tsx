import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import {
  getAccounts,
  getInsights,
  getFraudFlags,
  ApiError,
} from "../api/client";
import type {
  AccountWithTransactions,
  InsightsResponse,
  FraudFlag,
} from "../api/types";
import "./DashboardPage.css";

function formatMoney(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(value);
}

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function initials(email: string): string {
  return email.split("@")[0].slice(0, 2).toUpperCase();
}

export function DashboardPage() {
  const { token, userId, email, logout } = useAuth();
  const displayEmail = email ?? "User";
  const [activeSection, setActiveSection] = useState(
    () => window.location.hash.slice(1) || "overview",
  );

  useEffect(() => {
    const updateActiveSection = () => {
      setActiveSection(window.location.hash.slice(1) || "overview");
    };

    window.addEventListener("hashchange", updateActiveSection);
    return () => window.removeEventListener("hashchange", updateActiveSection);
  }, []);

  const [accounts, setAccounts] = useState<AccountWithTransactions[] | null>(
    null,
  );
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [fraudFlags, setFraudFlags] = useState<FraudFlag[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || userId === null) return;

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        try {
          const results = await Promise.allSettled([
            getAccounts(token!),
            getInsights(userId!, token!),
            getFraudFlags(userId!, token!),
          ]);

          if (cancelled) return;

          const [accountsResult, insightsResult, fraudResult] = results;
          const errors: string[] = [];

          if (accountsResult.status === "fulfilled") {
            setAccounts(accountsResult.value);
          } else {
            errors.push("Accounts failed to load.");
          }

          if (insightsResult.status === "fulfilled") {
            setInsights(insightsResult.value);
          } else {
            errors.push("Insights are currently unavailable.");
          }

          if (fraudResult.status === "fulfilled") {
            setFraudFlags(fraudResult.value.flags);
          } else {
            errors.push("Fraud detection failed to load.");
          }

          setError(errors.join(" "));
        } catch (err: unknown) {
          if (cancelled) return;

          setError(
            err instanceof Error ? err.message : "Unable to load dashboard.",
          );
        }
      } catch (err: unknown) {
        if (cancelled) return;

        if (err instanceof ApiError && err.status === 401) {
          logout();
          return;
        }

        setError(
          err instanceof Error ? err.message : "Failed to load dashboard data",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [token, userId, logout]);

  const allTransactions = useMemo(
    () =>
      (accounts ?? [])
        .flatMap(({ account, transactions }) =>
          transactions.map((transaction) => ({
            ...transaction,
            currency: account.currency,
          })),
        )
        .sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
        ),
    [accounts],
  );

  const totalBalance = (accounts ?? []).reduce(
    (sum, item) => sum + Number(item.account.balance),
    0,
  );

  const flaggedIds = new Set(
    (fraudFlags ?? []).map((flag) => flag.transaction_id),
  );

  const flaggedTotal = (fraudFlags ?? []).reduce(
    (sum, flag) => sum + Math.abs(Number(flag.amount)),
    0,
  );

  const uniqueFlaggedTransactions = new Set(
    (fraudFlags ?? []).map((flag) => flag.transaction_id),
  ).size;

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-mark">F</div>
        <p>Preparing your financial overview…</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/dashboard">
          finlens
        </a>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="side-nav" aria-label="Main navigation">
          <a
            className={`nav-item ${activeSection === "overview" ? "active" : ""}`}
            href="#overview"
          >
            <span className="nav-icon">▦</span> Overview
          </a>
          <a
            className={`nav-item ${activeSection === "security" ? "active" : ""}`}
            href="#security"
          >
            <span className="nav-icon">◇</span> Security
            {(fraudFlags?.length ?? 0) > 0 && (
              <span className="nav-count">{fraudFlags!.length}</span>
            )}
          </a>

          <a
            className={`nav-item ${activeSection === "transactions" ? "active" : ""}`}
            href="#transactions"
          >
            <span className="nav-icon">↔</span> Transactions
          </a>

          <a
            className={`nav-item ${activeSection === "insights" ? "active" : ""}`}
            href="#insights"
          >
            <span className="nav-icon">◷</span> Insights
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-user">
            <div className="avatar">{initials(displayEmail)}</div>
            <div className="user-copy">
              <strong>{displayEmail.split("@")[0]}</strong>
              <span>Personal workspace</span>
            </div>
            <button className="logout-button" onClick={logout} title="Sign out">
              ↗
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>Overview</strong>
          </div>
          <div className="topbar-right">
            <span className="live-indicator">
              <i /> Live data
            </span>
          </div>
        </header>

        <div className="dashboard-content" id="overview">
          {error && (
            <div className="error-banner" role="alert">
              <strong>We couldn’t refresh your dashboard.</strong>
              <span>{error}</span>
            </div>
          )}

          <section className="summary-grid" aria-label="Financial summary">
            <article className="summary-card balance-card">
              <div className="card-topline">
                <span className="summary-label">Combined account balances</span>
                <span className="metric-icon">€</span>
              </div>
              <div className="summary-value">
                {formatMoney(
                  totalBalance,
                  accounts?.[0]?.account.currency ?? "EUR",
                )}
              </div>
              <div className="summary-foot">
                <span className="metric-dot" />
                Across {accounts?.length ?? 0} account
                {(accounts?.length ?? 0) === 1 ? "" : "s"}
              </div>
            </article>

            <article className="summary-card">
              <div className="card-topline">
                <span className="summary-label">Transactions</span>
                <span className="metric-icon purple">↔</span>
              </div>
              <div className="summary-value">{allTransactions.length}</div>
              <div className="summary-foot">Available transaction records</div>
            </article>

            <article className="summary-card">
              <div className="card-topline">
                <span className="summary-label">Risk signals</span>
                <span className="metric-icon amber">⌁</span>
              </div>
              <div className="summary-value">{uniqueFlaggedTransactions}</div>
              <div className="summary-foot">
                {uniqueFlaggedTransactions > 0
                  ? "Transactions flagged for review"
                  : "No suspicious activity detected"}
              </div>
            </article>
          </section>

          <section className="section-block" id="security">
            <div className="section-heading">
              <div>
                <div className="eyebrow">MONITORING</div>
                <h2>Security overview</h2>
              </div>
              <span className="section-caption">Rule-based detection</span>
            </div>

            {fraudFlags && fraudFlags.length > 0 ? (
              <div className="fraud-panel">
                <div className="fraud-panel-header">
                  <div className="fraud-symbol">!</div>
                  <div className="fraud-title">
                    <div className="fraud-kicker">
                      ACTIVITY REQUIRES ATTENTION
                    </div>
                    <h3>Unusual transaction velocity</h3>
                    <p>
                      Multiple outgoing transactions occurred within a short
                      period. Review the activity to determine whether it is
                      expected.
                    </p>
                  </div>
                  <span className="risk-badge">Review recommended</span>
                </div>

                <div className="fraud-metrics">
                  <div>
                    <span>Flagged transactions</span>
                    <strong>{uniqueFlaggedTransactions}</strong>
                  </div>
                  <div>
                    <span>Combined flagged amount</span>
                    <strong>
                      {formatMoney(
                        flaggedTotal,
                        accounts?.find(
                          (item) =>
                            item.account.id === fraudFlags[0].account_id,
                        )?.account.currency ?? "EUR",
                      )}
                    </strong>
                  </div>
                  <div>
                    <span>Detection window</span>
                    <strong>
                      8 minutes <small>/ 10 min threshold</small>
                    </strong>
                  </div>
                </div>

                <div className="fraud-explanation">
                  <span className="explanation-icon">i</span>
                  <p>
                    <strong>Why was this flagged?</strong> The velocity rule
                    looks for at least five outgoing transactions within ten
                    minutes on the same account. This is a risk signal, not
                    confirmation of fraud.
                  </p>
                </div>

                <div className="flagged-list">
                  <div className="flagged-list-heading">
                    <strong>Flagged activity</strong>
                    <span>{uniqueFlaggedTransactions} records</span>
                  </div>
                  {fraudFlags.map((flag) => (
                    <div className="flagged-row" key={flag.transaction_id}>
                      <div className="transaction-symbol warning">↗</div>
                      <div className="flagged-description">
                        <strong>{flag.description}</strong>
                        <span>
                          {formatDate(flag.timestamp)} · {flag.category}
                        </span>
                      </div>
                      <span className="flag-reason">{flag.reason_detail}</span>
                      <strong className="flag-amount">
                        {formatMoney(
                          flag.amount,
                          accounts?.find(
                            (item) => item.account.id === flag.account_id,
                          )?.account.currency ?? "EUR",
                        )}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-panel">
                <span className="empty-check">✓</span>
                <div>
                  <strong>No risk signals detected</strong>
                  <p>
                    Your latest fraud check returned no flagged transactions.
                  </p>
                </div>
              </div>
            )}
          </section>

          <section className="section-block" id="transactions">
            <div className="section-heading">
              <div>
                <div className="eyebrow">ACCOUNT ACTIVITY</div>
                <h2>Recent transactions</h2>
              </div>
              <span className="section-caption">
                {allTransactions.length} records · newest first
              </span>
            </div>

            <div className="data-panel">
              <div className="table-scroll">
                <table className="transaction-table">
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Category</th>
                      <th>Date</th>
                      <th>Status</th>
                      <th className="amount-column">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allTransactions.slice(0, 10).map((tx) => (
                      <tr key={tx.id}>
                        <td>
                          <div className="transaction-cell">
                            <div
                              className={`transaction-symbol ${Number(tx.amount) < 0 ? "outgoing" : "incoming"}`}
                            >
                              {Number(tx.amount) < 0 ? "↗" : "↙"}
                            </div>
                            <div>
                              <strong>{tx.description}</strong>
                              <span>Account activity</span>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="category-pill">{tx.category}</span>
                        </td>
                        <td className="date-cell">
                          {formatDate(tx.timestamp)}
                        </td>
                        <td>
                          {flaggedIds.has(tx.id) ? (
                            <span className="status-pill flagged">Flagged</span>
                          ) : (
                            <span className="status-pill normal">Recorded</span>
                          )}
                        </td>
                        <td
                          className={`amount-column amount-cell ${Number(tx.amount) < 0 ? "negative" : "positive"}`}
                        >
                          {formatMoney(Number(tx.amount), tx.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {allTransactions.length === 0 && (
                  <div className="table-empty">
                    No transactions to display yet.
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="section-block" id="insights">
            <div className="section-heading">
              <div>
                <div className="eyebrow">SPENDING PATTERNS</div>
                <h2>Insights</h2>
              </div>
              <span className="section-caption">
                Based on available records
              </span>
            </div>

            {!insights ? (
              <div className="empty-panel">
                <div>
                  <strong>Insights unavailable</strong>
                  <p>We couldn't retrieve your spending insights.</p>
                </div>
              </div>
            ) : (
              <div className="insights-grid">
                <article className="insight-card">
                  <div className="insight-icon purple">⌁</div>
                  <h3>Spending alerts</h3>
                  {insights.spending_alerts.length > 0 ? (
                    insights.spending_alerts.map((alert) => (
                      <div className="insight-item" key={alert.category}>
                        <strong>{alert.category}</strong>
                        <span className="insight-highlight">
                          +{alert.increase_percent}%
                        </span>
                        <p>
                          {formatMoney(alert.current_month_total)} this month
                          <br />
                          <span>
                            Average: {formatMoney(alert.prior_average)}
                          </span>
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="muted-copy">
                      No spending alerts in the available data.
                    </p>
                  )}
                </article>

                <article className="insight-card">
                  <div className="insight-icon green">↻</div>
                  <h3>Subscriptions</h3>
                  {insights.subscriptions.length > 0 ? (
                    insights.subscriptions.map((sub, index) => (
                      <div
                        className="insight-item"
                        key={`${sub.description}-${index}`}
                      >
                        <strong>{sub.description}</strong>
                        <p>
                          {formatMoney(sub.amount)} · {sub.occurrences}{" "}
                          occurrences
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="muted-copy">
                      No recurring subscriptions detected.
                    </p>
                  )}
                </article>

                <article className="insight-card projection-card">
                  <div className="insight-icon amber">◷</div>
                  <h3>Balance projection</h3>
                  {insights.balance_projection ? (
                    <>
                      <div className="projection-value">
                        {Math.round(
                          insights.balance_projection.projected_days_until_zero,
                        )}
                        <span> days</span>
                      </div>
                      <p className="muted-copy">
                        Projected time until zero at the current average daily
                        net change of{" "}
                        {formatMoney(
                          insights.balance_projection.average_daily_net_change,
                        )}
                        .
                      </p>
                    </>
                  ) : (
                    <p className="muted-copy">
                      No zero-balance projection is available for the current
                      trend.
                    </p>
                  )}
                </article>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
