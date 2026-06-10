import type { MatchResponse } from '../types';
import { MatchCharts } from './MatchCharts';

interface MatchResultViewProps {
  onDownload: () => void;
  result: MatchResponse;
}

function skillList(skills: string[]) {
  if (!skills.length) {
    return <p className="empty">None</p>;
  }

  return (
    <ul>
      {skills.map((skill) => (
        <li key={skill}>{skill}</li>
      ))}
    </ul>
  );
}

export function MatchResultView({ onDownload, result }: MatchResultViewProps) {
  return (
    <>
      <section className="result-grid">
        <div className="metric-panel">
          <span>Match</span>
          <strong>{result.target_job_match.score}%</strong>
          <div className="meter">
            <div style={{ width: `${result.target_job_match.score}%` }} />
          </div>
        </div>
        <div className="metric-panel">
          <span>Matched skill weight</span>
          <strong>{result.target_job_match.matched_weight}</strong>
        </div>
        <div className="metric-panel">
          <span>Possible weight</span>
          <strong>{result.target_job_match.total_possible_weight}</strong>
        </div>
      </section>

      <MatchCharts breakdown={result.target_job_match.score_breakdown ?? []} />

      {result.target_job_match.score_breakdown?.length > 0 && (
        <section className="panel table-panel">
          <div className="panel-heading">
            <h2>Score explanation</h2>
            <span className="count">
              Final score = matched skill weight / possible weight * 100
            </span>
          </div>
          <div className="score-formula">
            <span>Final score:</span>
            <strong>{result.target_job_match.matched_weight}</strong>
            <span>/</span>
            <strong>{result.target_job_match.total_possible_weight}</strong>
            <span>* 100 =</span>
            <strong>{result.target_job_match.score}%</strong>
          </div>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Weight per skill</th>
                <th>Matched skills</th>
                <th>Category calculation</th>
                <th>Score contribution</th>
              </tr>
            </thead>
            <tbody>
              {result.target_job_match.score_breakdown.map((row) => (
                <tr key={row.category}>
                  <td>{row.label}</td>
                  <td>{row.weight}</td>
                  <td>{row.matched_count} of {row.total_count}</td>
                  <td>
                    <div className="category-calculation">
                      <span>Earned: {row.matched_count} × {row.weight} = {row.matched_weight}</span>
                      <span>Possible: {row.total_count} × {row.weight} = {row.total_weight}</span>
                    </div>
                  </td>
                  <td>
                    <div className="contribution-cell">
                      <div className="mini-meter">
                        <div style={{ width: `${Math.min(row.contribution_percent, 100)}%` }} />
                      </div>
                      <strong>{row.contribution_percent}%</strong>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="detail-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>Candidate profile</h2>
            <button className="ghost-button" type="button" onClick={onDownload}>
              Download JSON
            </button>
          </div>
          <div className="profile-line">
            <span>Email</span>
            <strong>{result.candidate_profile.email || 'Not found'}</strong>
          </div>
          <div className="profile-line">
            <span>Estimated experience</span>
            <strong>{result.candidate_profile.estimated_experience_years} years</strong>
          </div>
          <div className="chips">
            {result.candidate_profile.skills.map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </div>

        <div className="panel lists">
          <h2>Target match details</h2>
          <div>
            <h3>Matched strongly required skills</h3>
            {skillList(result.target_job_match.matched_strongly_required_skills)}
          </div>
          <div>
            <h3>Missing strongly required skills</h3>
            {skillList(result.target_job_match.missing_strongly_required_skills)}
          </div>
          <div>
            <h3>Matched skills</h3>
            {skillList(result.target_job_match.matched_skills)}
          </div>
          <div>
            <h3>Missing skills</h3>
            {skillList(result.target_job_match.missing_skills)}
          </div>
        </div>
      </section>

      {result.all_saved_job_matches.length > 0 && (
        <section className="panel table-panel">
          <h2>Match against all saved jobs</h2>
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>Match</th>
                <th>Matched strong skills</th>
                <th>Missing strong skills</th>
                <th>Matched skills</th>
                <th>Missing skills</th>
              </tr>
            </thead>
            <tbody>
              {result.all_saved_job_matches.map((row) => (
                <tr key={row.target_role}>
                  <td>{row.target_role}</td>
                  <td>{row.score}%</td>
                  <td>{row.matched_strongly_required_skills.length}</td>
                  <td>{row.missing_strongly_required_skills.length}</td>
                  <td>{row.matched_skills.length}</td>
                  <td>{row.missing_skills.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
