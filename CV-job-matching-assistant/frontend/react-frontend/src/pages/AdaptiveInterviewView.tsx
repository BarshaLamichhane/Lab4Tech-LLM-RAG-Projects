import type { ChangeEvent, RefObject } from 'react';

import type {
  AdaptiveInterviewResponse,
  GroundingIndexMode,
  InterviewContext,
  PreparationLevel,
  QuestionFocus,
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
  level: PreparationLevel;
  loadingLabel: string;
  maxTurns: number;
  onAnswerChange: (value: string) => void;
  onCodeChange: (value: string) => void;
  onCvBlur: () => void;
  onGenerationStrategyChange: (value: QuestionGenerationStrategy) => void;
  onGroundingIndexModeChange: (value: GroundingIndexMode) => void;
  onGroundingQueryChange: (value: string) => void;
  onLevelChange: (value: PreparationLevel) => void;
  onMaxTurnsChange: (value: number) => void;
  onRoleChange: (value: string) => void;
  onRestart: () => void;
  onSelectSkill: (focus: QuestionFocus, skill: string) => void;
  onStart: () => void;
  onSubmit: () => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  onUseCompanyContextChange: (value: boolean) => void;
  role: string;
  roles: string[];
  selectedFocus: QuestionFocus | null;
  selectedSkill: string;
  session: AdaptiveInterviewResponse | null;
  useCompanyContext: boolean;
}

export function AdaptiveInterviewView(props: Props) {
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
            {['Load CV and role', 'Choose one skill', 'Answer and score', 'Adapt difficulty', 'Review summary'].map((step, index) => (
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
              <label><span className="field-label">Question generation</span><select value={props.generationStrategy} onChange={(event) => props.onGenerationStrategyChange(event.target.value as QuestionGenerationStrategy)}><option value="llm">LLM only</option><option value="grounded">Grounded material</option></select></label>
              {props.generationStrategy === 'grounded' && <><label><span className="field-label">FAISS index mode</span><select value={props.groundingIndexMode} onChange={(event) => props.onGroundingIndexModeChange(event.target.value as GroundingIndexMode)}><option value="use_existing">Use existing</option><option value="update">Update</option><option value="recreate">Recreate</option></select></label><input placeholder="Optional grounding query" value={props.groundingQuery} onChange={(event) => props.onGroundingQueryChange(event.target.value)} /></>}
              {Object.keys(props.companyContext).length > 0 && <label className="check-row"><input type="checkbox" checked={props.useCompanyContext} onChange={(event) => props.onUseCompanyContextChange(event.target.checked)} /><span>Use company context</span></label>}
            </div>
          </section>
          {props.context && <section className="panel"><div className="section-intro"><h3>Choose one skill for the adaptive interview</h3><p>The next question becomes easier, deeper, or stays steady based on your validated score.</p></div><div className="skill-picker">{FOCUS_OPTIONS.filter((option) => (props.context?.skill_groups[option.value]?.length ?? 0) > 0).map((option) => <div className="skill-group-block" key={option.value}><span className={props.selectedFocus === option.value ? 'active-skill-label' : ''}>{option.label}</span><select value={props.selectedFocus === option.value ? props.selectedSkill : ''} onChange={(event) => props.onSelectSkill(option.value, event.target.value)}><option value="">Select skill</option>{(props.context?.skill_groups[option.value] ?? []).map((skill) => <option key={skill}>{skill}</option>)}</select></div>)}</div><button className="primary-button action-gap" disabled={!props.selectedSkill || Boolean(props.loadingLabel)} onClick={props.onStart}>Start Adaptive Interview</button></section>}
        </>
      )}

      {props.session?.finished && (
        <section className="adaptive-complete">
          <div className="panel final-summary">
            <p className="eyebrow">Interview complete</p>
            <h2>{props.session.state.selected_skills[0]} adaptive interview report</h2>
            <strong className="adaptive-score">
              {averageScore(props.session)}/10 average
            </strong>
            <p>
              {displaySummaryItem(props.session.final_summary?.summary)
                || 'Your adaptive interview is complete. Review each turn and continue practising the lowest-scoring areas.'}
            </p>
            <div className="adaptive-summary-grid">
              <SummaryList title="Strongest points" items={props.session.final_summary?.strongest_points} />
              <SummaryList title="Improvement areas" items={props.session.final_summary?.improvement_areas} />
              <SummaryList title="Recommended next steps" items={props.session.final_summary?.recommended_next_steps} />
            </div>
            <button className="primary-button" type="button" onClick={props.onRestart}>
              Start Another Adaptive Interview
            </button>
          </div>
          <div className="panel">
            <h2>Turn-by-turn results</h2>
            {props.session.state.turns.map((turn, index) => (
              <article className="adaptive-result-row" key={turn.question.id || index}>
                <div>
                  <span>Turn {index + 1} · {turn.question.difficulty}</span>
                  <strong>{turn.question.question}</strong>
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
            <div className="panel-heading"><div><p className="eyebrow">Turn {Math.min(completedTurns + 1, props.session.state.max_turns)} of {props.session.state.max_turns}</p><h2>{props.session.state.selected_skills[0]}</h2></div>{currentQuestion && <span className="score-badge">{currentQuestion.difficulty}</span>}</div>
            {currentQuestion && <><p className="question-text">{currentQuestion.question}</p>{currentQuestion.is_coding && <textarea className="code-editor" value={props.code} onChange={(event) => props.onCodeChange(event.target.value)} placeholder="Write Python code..." />}<textarea value={props.answer} onChange={(event) => props.onAnswerChange(event.target.value)} placeholder={currentQuestion.is_coding ? 'Optional explanation' : 'Your answer'} /><button className="primary-button action-gap" disabled={Boolean(props.loadingLabel) || (!props.answer.trim() && !props.code.trim())} onClick={props.onSubmit}>Score Answer and Adapt</button></>}
          </div>
          <div className="panel"><h2>Live feedback</h2>{latestEvaluation ? <><strong className="adaptive-score">{latestEvaluation.score}/10</strong><p>{latestEvaluation.feedback}</p><div className="chips">{(latestEvaluation.strengths ?? []).map((item) => <span key={item}>{item}</span>)}</div></> : <p className="muted-line">Feedback appears after your first answer.</p>}<h3>Progression</h3>{props.session.state.turns.map((turn, index) => <div className="adaptive-turn" key={turn.question.id || index}><span>Turn {index + 1} · {turn.question.difficulty}</span><strong>{turn.evaluation ? `${turn.evaluation.score}/10` : 'Current'}</strong></div>)}</div>
        </section>
      )}

      {(props.loadingLabel || props.error) && <section className="status-row">{props.loadingLabel && <div className="status loading">{props.loadingLabel}...</div>}{props.error && <div className="status error">{props.error}</div>}</section>}
    </>
  );
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

const FOCUS_OPTIONS: { label: string; value: QuestionFocus }[] = [
  { label: 'Matched strongly required', value: 'matched_strongly_required' },
  { label: 'Matched skills', value: 'matched_skills' },
  { label: 'Missing strongly required', value: 'missing_strongly_required' },
  { label: 'Missing skills', value: 'missing_skills' },
  { label: 'Matched tools', value: 'matched_tools' },
  { label: 'Missing tools', value: 'missing_tools' },
  { label: 'Soft skills', value: 'soft_skills' },
  { label: 'Responsibilities', value: 'responsibilities' },
];
