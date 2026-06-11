import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { changePassword } from '../api';
import { useAuth } from '../AuthContext';
import { errorMessage } from '../ui';

export function AccountPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (newPassword !== confirmation) {
      setError('New passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      await logout();
      navigate('/login', { replace: true });
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
          <p className="eyebrow">Account</p>
          <h1>Security settings</h1>
        </div>
      </section>
      <section className="auth-shell account-shell">
        <form className="panel auth-panel" onSubmit={submit}>
          <h2>Change password</h2>
          <p className="muted-line">Signed in as {user?.username}. Changing your password signs out existing sessions.</p>
          <label className="field-label" htmlFor="current-password">Current password</label>
          <input id="current-password" className="number-input" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} />
          <label className="field-label" htmlFor="new-password">New password</label>
          <input id="new-password" className="number-input" minLength={12} type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} />
          <label className="field-label" htmlFor="confirm-password">Confirm new password</label>
          <input id="confirm-password" className="number-input" minLength={12} type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
          {error && <div className="status error">{error}</div>}
          <button className="primary-button action-gap" disabled={loading} type="submit">
            {loading ? 'Updating password...' : 'Update password'}
          </button>
        </form>
      </section>
    </>
  );
}
