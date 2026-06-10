import { useEffect, useState } from 'react';

import { getUserSessions } from '../api';
import type { UserSession } from '../types';
import { errorMessage } from '../ui';

export function SessionHistoryPage() {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    getUserSessions().then(setSessions).catch((caughtError) => setError(errorMessage(caughtError)));
  }, []);

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">My activity</p>
          <h1>Saved sessions</h1>
        </div>
      </section>
      {error && <section className="status-row"><div className="status error">{error}</div></section>}
      <section className="session-grid">
        {sessions.map((session) => (
          <article className="session-item" key={session.id}>
            <span>{session.session_type.replaceAll('_', ' ')}</span>
            <h2>{session.title}</h2>
            <p>{new Date(session.created_at).toLocaleString()}</p>
          </article>
        ))}
        {!sessions.length && !error && <div className="panel empty">No saved sessions yet.</div>}
      </section>
    </>
  );
}
