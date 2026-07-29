import { useAuth } from '../auth/AuthContext';

export function DashboardPage() {
  const { email, logout } = useAuth();

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: '0 16px' }}>
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
      <p>Welcome to Finlens. Your accounts and insights will appear here.</p>
    </div>
  );
}