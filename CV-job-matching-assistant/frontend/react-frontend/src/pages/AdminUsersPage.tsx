import { FormEvent, useState } from 'react';

import { createUser } from '../api';
import type { AuthUser } from '../types';
import { errorMessage } from '../ui';

export function AdminUsersPage() {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<AuthUser['role']>('user');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus('');
    setError('');
    if (password !== confirmation) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const created = await createUser(username, password, role);
      setStatus(`${created.role === 'admin' ? 'Admin' : 'User'} account "${created.username}" created.`);
      setUsername('');
      setRole('user');
      setPassword('');
      setConfirmation('');
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Create an account</h1>
        </div>
      </section>
      <section className="auth-shell account-shell">
        <form className="panel auth-panel" onSubmit={submit}>
          <h2>New user or administrator</h2>
          <p className="muted-line">Administrators can manage settings. Users can run matching and interview practice.</p>

          <label className="field-label" htmlFor="new-username">Username</label>
          <input id="new-username" autoComplete="off" className="number-input" minLength={3} required value={username} onChange={(event) => setUsername(event.target.value)} />

          <label className="field-label" htmlFor="new-role">Account role</label>
          <select id="new-role" value={role} onChange={(event) => setRole(event.target.value as AuthUser['role'])}>
            <option value="user">User</option>
            <option value="admin">Administrator</option>
          </select>

          <label className="field-label" htmlFor="new-user-password">Initial password</label>
          <input id="new-user-password" autoComplete="new-password" className="number-input" minLength={12} required type="password" value={password} onChange={(event) => setPassword(event.target.value)} />

          <label className="field-label" htmlFor="new-user-confirmation">Confirm password</label>
          <input id="new-user-confirmation" autoComplete="new-password" className="number-input" minLength={12} required type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />

          {status && <div className="status loading">{status}</div>}
          {error && <div className="status error">{error}</div>}
          <button className="primary-button action-gap" disabled={loading} type="submit">
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
      </section>
    </>
  );
}
