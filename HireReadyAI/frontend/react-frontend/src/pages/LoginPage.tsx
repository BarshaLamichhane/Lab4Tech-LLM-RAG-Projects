import { FormEvent, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { useAuth } from '../AuthContext';
import { errorMessage } from '../ui';

export function LoginPage() {
  const { user, isLoading, login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isLoading) {
    return <section className="status-row"><div className="status loading">Checking session...</div></section>;
  }

  if (!isLoading && user) {
    return <Navigate to="/" replace />;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-shell">
      <form className="panel auth-panel" onSubmit={submit}>
        <p className="eyebrow">HireReadyAI</p>
        <h1>Sign in to continue</h1>
        <label className="field-label" htmlFor="username">Username</label>
        <input id="username" className="number-input" value={username} onChange={(event) => setUsername(event.target.value)} />
        <label className="field-label" htmlFor="password">Password</label>
        <input id="password" className="number-input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        {error && <div className="status error">{error}</div>}
        <button className="primary-button action-gap" disabled={loading} type="submit">
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
        <p className="login-hint">Your secure session expires automatically. Contact an administrator if you need an account.</p>
      </form>
    </section>
  );
}
