import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getAdaptiveProgress } from '../api';
import type { AdaptiveProgressDashboard } from '../types';
import { errorMessage } from '../ui';

export function AdaptiveProgressPage() {
  const [dashboard, setDashboard] = useState<AdaptiveProgressDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getAdaptiveProgress().then(setDashboard).catch((caughtError) => setError(errorMessage(caughtError)));
  }, []);

  if (error) return <section className="status-row"><div className="status error">{error}</div></section>;
  if (!dashboard) return <section className="status-row"><div className="status loading">Loading adaptive progress...</div></section>;

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Adaptive Interview</p>
          <h1>Adaptive progress dashboard</h1>
        </div>
        <Link className="primary-button" to="/adaptive-interview">Start adaptive session</Link>
      </section>

      <section className="result-grid">
        <div className="metric-panel"><span>Adaptive sessions</span><strong>{dashboard.sessions}</strong></div>
        <div className="metric-panel"><span>Answered</span><strong>{dashboard.answered_questions}</strong></div>
        <div className="metric-panel"><span>Average score</span><strong>{dashboard.overall_average}/10</strong></div>
        <div className="metric-panel"><span>Latest readiness</span><strong>{dashboard.latest_readiness_score}%</strong></div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Average score by adaptive skill</h2>
          <ScoreBars items={dashboard.average_by_skill.map((item) => ({ label: `${item.skill} (${item.attempts})`, score: item.average_score }))} />
        </div>
        <div className="panel">
          <h2>Learner profile status</h2>
          <div className="adaptive-status-grid">
            <div><span>Weak</span><strong>{dashboard.skill_status_counts.weak}</strong></div>
            <div><span>Developing</span><strong>{dashboard.skill_status_counts.developing}</strong></div>
            <div><span>Strong</span><strong>{dashboard.skill_status_counts.strong}</strong></div>
          </div>
        </div>
        <div className="panel">
          <h2>Strongest adaptive skills</h2>
          <SkillChips skills={dashboard.strongest_skills} empty="Complete an adaptive session to discover strengths." />
        </div>
        <div className="panel">
          <h2>Weakest adaptive skills</h2>
          <SkillChips skills={dashboard.weakest_skills} empty="No weak adaptive skills identified yet." />
        </div>
      </section>

      <section className="panel table-panel">
        <h2>Readiness trend</h2>
        <div className="trend-list">
          {dashboard.readiness_trend.map((item) => (
            <div key={`${item.date}-${item.role}`}>
              <span>{new Date(item.date).toLocaleDateString()}</span>
              <strong>{item.role}</strong>
              <b>{item.readiness_score}% · {item.average_score}/10</b>
            </div>
          ))}
          {!dashboard.readiness_trend.length && <p className="muted-line">No completed adaptive sessions yet.</p>}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Saved adaptive reports</h2>
          <div className="retry-list">
            {dashboard.recent_reports.map((report) => (
              <article key={report.session_id}>
                <span>{new Date(report.date).toLocaleDateString()} · {report.average_score}/10 · {report.readiness_score}% ready</span>
                <strong>{report.title}</strong>
                <p>{report.summary || 'Adaptive report saved.'}</p>
              </article>
            ))}
            {!dashboard.recent_reports.length && <p className="muted-line">No saved adaptive reports yet.</p>}
          </div>
        </div>
        <div className="panel next-session">
          <p className="eyebrow">Recommended next adaptive session</p>
          <h2>{dashboard.recommended_next_session.skills.join(', ') || 'Complete one adaptive session'}</h2>
          <p>{dashboard.recommended_next_session.reason}</p>
          <Link className="primary-button" to="/adaptive-interview">Continue adaptive practice</Link>
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
    {!items.length && <p className="muted-line">No adaptive scores yet.</p>}
  </div>;
}

function SkillChips({ skills, empty }: { skills: string[]; empty: string }) {
  return <div className="chips">
    {skills.map((skill) => <span key={skill}>{skill}</span>)}
    {!skills.length && <p className="muted-line">{empty}</p>}
  </div>;
}
