import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getInterviewProgress } from '../api';
import type { InterviewProgressDashboard } from '../types';
import { errorMessage } from '../ui';

export function InterviewProgressPage() {
  const [dashboard, setDashboard] = useState<InterviewProgressDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getInterviewProgress().then(setDashboard).catch((caughtError) => setError(errorMessage(caughtError)));
  }, []);

  if (error) return <section className="status-row"><div className="status error">{error}</div></section>;
  if (!dashboard) return <section className="status-row"><div className="status loading">Loading progress...</div></section>;

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Interview Assistant</p>
          <h1>Progress dashboard</h1>
        </div>
        <Link className="primary-button" to="/interview-practice">Start practice</Link>
      </section>

      <section className="result-grid">
        <div className="metric-panel"><span>Sessions</span><strong>{dashboard.sessions}</strong></div>
        <div className="metric-panel"><span>Answered</span><strong>{dashboard.answered_questions}</strong></div>
        <div className="metric-panel"><span>Average</span><strong>{dashboard.overall_average}/10</strong></div>
        <div className="metric-panel"><span>Retry queue</span><strong>{dashboard.retry_questions.length}</strong></div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Average score by skill</h2>
          <ScoreBars items={dashboard.average_by_skill.map((item) => ({ label: item.skill, score: item.average_score }))} />
        </div>
        <div className="panel">
          <h2>Coding versus theory</h2>
          <ScoreBars items={dashboard.average_by_type.map((item) => ({ label: item.type.replaceAll('_', ' '), score: item.average_score }))} />
        </div>
        <div className="panel">
          <h2>Strongest topics</h2>
          <TopicList items={dashboard.strongest_topics} empty="Complete a scored question to discover strengths." />
        </div>
        <div className="panel">
          <h2>Weakest topics</h2>
          <TopicList items={dashboard.weakest_topics} empty="No weak topics identified yet." />
        </div>
      </section>

      <section className="panel table-panel">
        <h2>Score trend</h2>
        <div className="trend-list">
          {dashboard.score_trend.map((item) => (
            <div key={`${item.date}-${item.role}`}>
              <span>{new Date(item.date).toLocaleDateString()}</span>
              <strong>{item.role}</strong>
              <b>{item.average_score}/10</b>
            </div>
          ))}
          {!dashboard.score_trend.length && <p className="muted-line">No scored sessions yet.</p>}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Questions requiring another attempt</h2>
          <div className="retry-list">
            {dashboard.retry_questions.map((item) => (
              <article key={`${item.session_id}-${item.question_id}`}>
                <span>{item.skill} · {item.score}/10</span>
                <p>{item.question}</p>
              </article>
            ))}
            {!dashboard.retry_questions.length && <p className="muted-line">Nothing in the retry queue.</p>}
          </div>
        </div>
        <div className="panel next-session">
          <p className="eyebrow">Recommended next session</p>
          <h2>{dashboard.recommended_next_session.skills.join(', ')}</h2>
          <p>{dashboard.recommended_next_session.reason}</p>
          <Link className="primary-button" to="/interview-practice">Practise these topics</Link>
        </div>
      </section>
    </>
  );
}

function ScoreBars({ items }: { items: { label: string; score: number }[] }) {
  return <div className="dashboard-bars">
    {items.map((item) => <div key={item.label}>
      <span>{item.label}</span><strong>{item.score}/10</strong>
      <progress max={10} value={item.score} />
    </div>)}
    {!items.length && <p className="muted-line">No scored answers yet.</p>}
  </div>;
}

function TopicList({ items, empty }: { items: { skill: string; average_score: number }[]; empty: string }) {
  return <div className="topic-rank-list">
    {items.map((item) => <div key={item.skill}><strong>{item.skill}</strong><span>{item.average_score}/10</span></div>)}
    {!items.length && <p className="muted-line">{empty}</p>}
  </div>;
}
