import { useState, type ChangeEvent, type RefObject } from 'react';
import { jsPDF } from 'jspdf';

import type {
  AdaptiveInterviewResponse,
  AdaptiveStartFocus,
  GroundingIndexMode,
  GroundingSource,
  InterviewContext,
  PreparationLevel,
  QuestionGenerationStrategy,
} from '../types';

interface Props {
  answer: string;
  code: string;
  companyContext: Record<string, string>;
  context: InterviewContext | null;
  cvTextRef: RefObject<HTMLTextAreaElement | null>;
  error: string;
  generationStrategy: QuestionGenerationStrategy;
  groundingIndexMode: GroundingIndexMode;
  groundingQuery: string;
  groundingSources: GroundingSource[];
  level: PreparationLevel;
  loadingLabel: string;
  maxTurns: number;
  onAddGroundingUrl: (url: string) => void;
  onAnswerChange: (value: string) => void;
  onBuildGroundingIndex: () => void;
  onCodeChange: (value: string) => void;
  onCvBlur: () => void;
  onGenerationStrategyChange: (value: QuestionGenerationStrategy) => void;
  onGroundingIndexModeChange: (value: GroundingIndexMode) => void;
  onGroundingQueryChange: (value: string) => void;
  onLevelChange: (value: PreparationLevel) => void;
  onMaxTurnsChange: (value: number) => void;
  onStartFocusChange: (value: AdaptiveStartFocus) => void;
  onRoleChange: (value: string) => void;
  onRestart: () => void;
  onStart: () => void;
  onSubmit: () => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  onUploadGrounding: (event: ChangeEvent<HTMLInputElement>) => void;
  onUseCompanyContextChange: (value: boolean) => void;
  role: string;
  roles: string[];
  session: AdaptiveInterviewResponse | null;
  startFocus: AdaptiveStartFocus;
  useCompanyContext: boolean;
}

export function AdaptiveInterviewView(props: Props) {
  const [groundingUrl, setGroundingUrl] = useState('');
  const currentQuestion = props.session?.next_question;
  const completedTurns = props.session?.state.turns.filter((turn) => turn.evaluation).length ?? 0;
  const latestEvaluation = [...(props.session?.state.turns ?? [])].reverse().find((turn) => turn.evaluation)?.evaluation;

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Adaptive Interview</p>
          <h1>Let each answer shape the next question</h1>
        </div>
      </section>

      {!props.session && (
        <>
          <section className="adaptive-flow">
            {['Load CV and role', 'Build learner profile', 'Ask weakest skill', 'Adapt next skill', 'Review readiness'].map((step, index) => (
              <div key={step}><strong>{index + 1}</strong><span>{step}</span></div>
            ))}
          </section>
          <section className="input-grid">
            <div className="panel">
              <div className="panel-heading">
                <h2>Candidate CV</h2>
                <label className="file-control"><span>Upload</span><input type="file" accept=".txt,.pdf" onChange={props.onUploadCv} /></label>
              </div>
              <textarea ref={props.cvTextRef} onBlur={props.onCvBlur} />
            </div>
            <div className="panel adaptive-config">
              <h2>Interview setup</h2>
              <label><span className="field-label">Saved role</span><select value={props.role} onChange={(event) => props.onRoleChange(event.target.value)}>{props.roles.map((role) => <option key={role}>{role}</option>)}</select></label>
              <div className="interview-config-grid">
                <label><span className="field-label">Starting level</span><select value={props.level} onChange={(event) => props.onLevelChange(event.target.value as PreparationLevel)}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label>
                <label><span className="field-label">Turns</span><input type="number" min={2} max={10} value={props.maxTurns} onChange={(event) => props.onMaxTurnsChange(Number(event.target.value))} /></label>
              </div>
              <label><span className="field-label">Start from</span><select value={props.startFocus} onChange={(event) => props.onStartFocusChange(event.target.value as AdaptiveStartFocus)}><option value="weak">Highest-priority weak skill</option><option value="strong">Highest-priority strong skill</option></select></label>
              <label><span className="field-label">Question generation</span><select value={props.generationStrategy} onChange={(event) => props.onGenerationStrategyChange(event.target.value as QuestionGenerationStrategy)}><option value="llm">LLM only</option><option value="grounded">Grounded material</option></select></label>
              {props.generationStrategy === 'grounded' && (
                <div className="grounding-controls compact-grounding">
                  <div className="grounding-action-row">
                    <label className="file-control">
                      <span>Upload verified material</span>
                      <input multiple type="file" accept=".pdf,.txt,.md,.xml" onChange={props.onUploadGrounding} />
                    </label>
                    <select
                      value={props.groundingIndexMode}
                      onChange={(event) => props.onGroundingIndexModeChange(event.target.value as GroundingIndexMode)}
                    >
                      <option value="use_existing">Use existing index</option>
                      <option value="update">Update index</option>
                      <option value="recreate">Recreate index</option>
                    </select>
                    <button className="ghost-button" type="button" disabled={Boolean(props.loadingLabel)} onClick={props.onBuildGroundingIndex}>
                      Prepare index
                    </button>
                  </div>
                  <div className="grounding-action-row">
                    <input
                      placeholder="HTTPS link to verified material"
                      value={groundingUrl}
                      onChange={(event) => setGroundingUrl(event.target.value)}
                    />
                    <button
                      className="ghost-button"
                      type="button"
                      disabled={!groundingUrl.trim() || Boolean(props.loadingLabel)}
                      onClick={() => {
                        props.onAddGroundingUrl(groundingUrl.trim());
                        setGroundingUrl('');
                      }}
                    >
                      Add link
                    </button>
                  </div>
                  <label><span className="field-label">Optional grounding query</span><input placeholder="e.g. LangGraph checkpoints or company policy" value={props.groundingQuery} onChange={(event) => props.onGroundingQueryChange(event.target.value)} /></label>
                  <div className="grounding-source-list">
                    <strong>Selected grounding sources</strong>
                    {props.groundingSources.map((source) => (
                      <span key={source.filename}>
                        {source.filename} {source.indexed ? `· ${source.chunk_count} chunks` : '· not indexed'}
                      </span>
                    ))}
                    {!props.groundingSources.length && <small>No verified material uploaded.</small>}
                  </div>
                </div>
              )}
              {Object.keys(props.companyContext).length > 0 && <label className="check-row"><input type="checkbox" checked={props.useCompanyContext} onChange={(event) => props.onUseCompanyContextChange(event.target.checked)} /><span>Use company context</span></label>}
            </div>
          </section>
          {props.context && (
            <section className="panel adaptive-profile-preview">
              <div className="section-intro">
                <h3>Learner profile ready</h3>
                <p>{props.startFocus === 'weak' ? 'The system will start from the highest-priority weak skill and switch skills based on your score.' : 'The system will start by validating your highest-priority strong skill, then switch skills based on your score.'}</p>
              </div>
              <div className="adaptive-profile-grid">
                <div>
                  <span className="field-label">Role readiness</span>
                  <strong className="adaptive-score compact">{Number(props.context.match_result?.score ?? 0)}%</strong>
                </div>
                <SkillPreview title="Weakest targets" skills={previewSkills(props.context, ['missing_strongly_required', 'missing_required', 'missing_skills', 'missing_tools'])} />
                <SkillPreview title="Current strengths" skills={previewSkills(props.context, ['matched_strongly_required', 'matched_required', 'matched_skills', 'matched_tools'])} />
              </div>
              <button className="primary-button action-gap" disabled={Boolean(props.loadingLabel)} onClick={props.onStart}>
                Start Adaptive Interview
              </button>
            </section>
          )}
        </>
      )}

      {props.session?.finished && (
        <section className="adaptive-complete">
          <div className="panel final-summary">
            <p className="eyebrow">Interview complete</p>
            <h2>{props.session.state.role} adaptive interview report</h2>
            <strong className="adaptive-score">
              {averageScore(props.session)}/10 average
            </strong>
            {props.session.state.learner_profile && (
              <div className="adaptive-profile-grid">
                <SkillPreview title="Strongest skills" skills={props.session.state.learner_profile.strongest_skills} />
                <SkillPreview title="Weakest skills" skills={props.session.state.learner_profile.weakest_skills} />
                <div>
                  <span className="field-label">Readiness</span>
                  <strong className="adaptive-score compact">{props.session.state.learner_profile.readiness_score}%</strong>
                </div>
              </div>
            )}
            <p>
              {displaySummaryItem(props.session.final_summary?.summary)
                || 'Your adaptive interview is complete. Review each turn and continue practising the lowest-scoring areas.'}
            </p>
            <div className="adaptive-summary-grid">
              <SummaryList title="Strongest points" items={props.session.final_summary?.strongest_points} />
              <SummaryList title="Improvement areas" items={props.session.final_summary?.improvement_areas} />
              <SummaryList title="Recommended next steps" items={props.session.final_summary?.recommended_next_steps} />
            </div>
            <div className="button-row">
              <button className="primary-button" type="button" onClick={() => downloadAdaptiveReportPdf(props.session!)}>
                Download adaptive report PDF
              </button>
              <button className="ghost-button" type="button" onClick={props.onRestart}>
                Start Another Adaptive Interview
              </button>
            </div>
          </div>
          <div className="panel">
            <h2>Turn-by-turn results</h2>
            {props.session.state.turns.map((turn, index) => (
              <article className="adaptive-result-row" key={turn.question.id || index}>
                <div>
                  <span>Turn {index + 1} · {turn.question.difficulty}</span>
                  <strong>{turn.question.skill}: {turn.question.question}</strong>
                </div>
                <strong className="score-badge">{turn.evaluation?.score ?? '-'}/10</strong>
                <p>{turn.evaluation?.feedback || 'No feedback available.'}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {props.session && !props.session.finished && (
        <section className="adaptive-session-grid">
          <div className="panel">
            <div className="panel-heading"><div><p className="eyebrow">Turn {Math.min(completedTurns + 1, props.session.state.max_turns)} of {props.session.state.max_turns}</p><h2>{currentQuestion?.skill ?? props.session.state.current_skill}</h2>{props.session.state.current_decision_reason && <p className="muted-line">{props.session.state.current_decision_reason}</p>}</div>{currentQuestion && <span className="score-badge">{currentQuestion.difficulty}</span>}</div>
            {currentQuestion && <><p className="question-text">{currentQuestion.question}</p>{currentQuestion.is_coding && <textarea className="code-editor" value={props.code} onChange={(event) => props.onCodeChange(event.target.value)} placeholder="Write Python code..." />}<textarea value={props.answer} onChange={(event) => props.onAnswerChange(event.target.value)} placeholder={currentQuestion.is_coding ? 'Optional explanation' : 'Your answer'} /><button className="primary-button action-gap" disabled={Boolean(props.loadingLabel) || (!props.answer.trim() && !props.code.trim())} onClick={props.onSubmit}>Score Answer and Adapt</button></>}
          </div>
          <div className="panel"><h2>Live feedback</h2>{latestEvaluation ? <><strong className="adaptive-score">{latestEvaluation.score}/10</strong><p>{latestEvaluation.feedback}</p><div className="chips">{(latestEvaluation.strengths ?? []).map((item) => <span key={item}>{item}</span>)}</div></> : <p className="muted-line">Feedback appears after your first answer.</p>}<h3>Progression</h3>{props.session.state.turns.map((turn, index) => <div className="adaptive-turn" key={turn.question.id || index}><span>Turn {index + 1} · {turn.question.skill} · {turn.question.difficulty}</span><strong>{turn.evaluation ? `${turn.evaluation.score}/10` : 'Current'}</strong></div>)}</div>
        </section>
      )}

      {(props.loadingLabel || props.error) && <section className="status-row">{props.loadingLabel && <div className="status loading">{props.loadingLabel}...</div>}{props.error && <div className="status error">{props.error}</div>}</section>}
    </>
  );
}

function SkillPreview({ title, skills }: { title: string; skills: string[] }) {
  return (
    <div>
      <span className="field-label">{title}</span>
      <div className="chips">
        {skills.length > 0
          ? skills.slice(0, 5).map((skill) => <span key={`${title}-${skill}`}>{skill}</span>)
          : <span>No skills found</span>}
      </div>
    </div>
  );
}

function previewSkills(context: InterviewContext, groups: string[]): string[] {
  const seen = new Set<string>();
  const skillGroups = context.skill_groups as Record<string, string[] | undefined>;
  return groups.flatMap((group) => skillGroups[group] ?? []).filter((skill) => {
    const normalized = skill.toLowerCase();
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

function SummaryList({ title, items }: { title: string; items?: unknown[] }) {
  const displayItems = (items ?? []).map(displaySummaryItem).filter(Boolean);
  return (
    <div>
      <h3>{title}</h3>
      {displayItems.length > 0
        ? displayItems.map((item, index) => <span key={`${title}-${index}`}>{item}</span>)
        : <p className="muted-line">No details provided.</p>}
    </div>
  );
}

function displaySummaryItem(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(displaySummaryItem).filter(Boolean).join(', ');
  if (value && typeof value === 'object') {
    return Object.entries(value)
      .map(([key, item]) => `${titleCase(key)}: ${displaySummaryItem(item)}`)
      .filter((item) => !item.endsWith(': '))
      .join(' | ');
  }
  return value == null ? '' : String(value);
}

function titleCase(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function averageScore(session: AdaptiveInterviewResponse): number {
  const scores = session.state.turns.flatMap((turn) =>
    typeof turn.evaluation?.score === 'number' ? [turn.evaluation.score] : [],
  );
  if (!scores.length) return 0;
  return Math.round((scores.reduce((total, score) => total + score, 0) / scores.length) * 10) / 10;
}

function downloadAdaptiveReportPdf(session: AdaptiveInterviewResponse) {
  const document = new jsPDF({ unit: 'pt', format: 'a4' });
  const left = 48;
  const width = document.internal.pageSize.getWidth() - left * 2;
  const pageBottom = document.internal.pageSize.getHeight() - 48;
  let y = 52;

  function write(text: string, options: { bold?: boolean; size?: number; gap?: number } = {}) {
    const size = options.size ?? 10;
    document.setFont('helvetica', options.bold ? 'bold' : 'normal');
    document.setFontSize(size);
    const lines = document.splitTextToSize(text || '-', width) as string[];
    const lineHeight = size * 1.35;
    if (y + lines.length * lineHeight > pageBottom) {
      document.addPage();
      y = 52;
    }
    document.text(lines, left, y);
    y += lines.length * lineHeight + (options.gap ?? 6);
  }

  write(`${session.state.role} Adaptive Interview Report`, { bold: true, size: 18, gap: 10 });
  write(
    `Average score: ${averageScore(session)}/10 | Readiness: ${session.state.learner_profile?.readiness_score ?? 0}% | Answered: ${session.state.turns.filter((turn) => turn.evaluation).length}/${session.state.max_turns}`,
    { gap: 12 },
  );
  write(`Start mode: ${session.state.start_focus === 'strong' ? 'Highest-priority strong skill' : 'Highest-priority weak skill'}`, { gap: 14 });

  const summary = displaySummaryItem(session.final_summary?.summary);
  if (summary) {
    write('Final summary', { bold: true, size: 14, gap: 4 });
    write(summary, { gap: 12 });
  }

  const strongest = session.state.learner_profile?.strongest_skills ?? [];
  const weakest = session.state.learner_profile?.weakest_skills ?? [];
  if (strongest.length || weakest.length) {
    write('Learner profile', { bold: true, size: 14, gap: 4 });
    write(`Strongest skills: ${strongest.join(', ') || '-'}`);
    write(`Weakest skills: ${weakest.join(', ') || '-'}`, { gap: 12 });
  }

  session.state.turns.forEach((turn, index) => {
    const evaluation = turn.evaluation;
    write(`Turn ${index + 1}: ${turn.question.skill ?? 'General'} (${turn.question.difficulty})`, { bold: true, size: 13, gap: 4 });
    if (turn.decision_reason) {
      write(`Why this question: ${turn.decision_reason}`, { gap: 4 });
    }
    write(`Question: ${turn.question.question}`, { gap: 8 });
    write('User answer', { bold: true, gap: 2 });
    write(turn.answer || 'Not answered', { gap: 8 });
    write(`Score: ${evaluation?.score ?? '-'}/10`, { bold: true, gap: 2 });
    write(`Feedback: ${evaluation?.feedback || 'Not scored'}`, { gap: 6 });
    if (evaluation?.strengths?.length) {
      write(`Strengths: ${evaluation.strengths.join('; ')}`, { gap: 4 });
    }
    if (evaluation?.weaknesses?.length) {
      write(`Weaknesses: ${evaluation.weaknesses.join('; ')}`, { gap: 4 });
    }
    if (evaluation?.learning_recommendations?.length) {
      write(`Learning recommendations: ${evaluation.learning_recommendations.join('; ')}`, { gap: 4 });
    }
    y += 8;
  });

  const nextSteps = (session.final_summary?.recommended_next_steps ?? []).map(displaySummaryItem).filter(Boolean);
  if (nextSteps.length) {
    write('Recommended next steps', { bold: true, size: 14, gap: 4 });
    nextSteps.forEach((step) => write(`- ${step}`, { gap: 2 }));
  }

  document.save(`${adaptiveReportFilename(session.state.role)}-adaptive-interview-report.pdf`);
}

function adaptiveReportFilename(role: string) {
  return role.toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'adaptive-interview';
}
