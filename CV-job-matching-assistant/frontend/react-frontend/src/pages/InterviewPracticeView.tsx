import { ChangeEvent, RefObject, useEffect, useState } from 'react';
import { jsPDF } from 'jspdf';
import { Link } from 'react-router-dom';

import type {
  AnswerEvaluation,
  CodeRunResponse,
  InterviewPlan,
  InterviewPracticeSession,
  InterviewQuestion,
  LearningPathItem,
  PreparationInterviewType,
  PreparationLevel,
  QuestionFocus,
} from '../types';

interface InterviewPracticeViewProps {
  activeSessionId: string;
  answerRef: RefObject<HTMLTextAreaElement | null>;
  answerValue: string;
  answersByQuestion: Record<string, string>;
  averageScore: number | null;
  bookmarked: boolean;
  currentEvaluation: AnswerEvaluation | null;
  currentQuestion: InterviewQuestion | null;
  currentQuestionIndex: number;
  codeRunResult: CodeRunResponse | null;
  codeByQuestion: Record<string, string>;
  codeValue: string;
  cvTextRef: RefObject<HTMLTextAreaElement | null>;
  error: string;
  elapsedSeconds: number;
  evaluations: Record<string, AnswerEvaluation>;
  learningPath: LearningPathItem[];
  loading: boolean;
  loadingLabel: string;
  noteValue: string;
  onCvBlur: () => void;
  onEvaluateAnswer: () => void;
  onGeneratePlan: () => void;
  onRegenerateQuestion: () => void;
  onReportQuestion: (reason: 'irrelevant' | 'poor_quality') => void;
  onRetryQuestion: () => void;
  onToggleBookmark: () => void;
  onNextQuestion: () => void;
  onPauseSession: () => void;
  onCompleteSession: () => void;
  onPreviousQuestion: () => void;
  onQuestionCountChange: (count: number) => void;
  onPreparationLevelChange: (level: PreparationLevel) => void;
  onInterviewTypeChange: (interviewType: PreparationInterviewType) => void;
  onQuestionFocusClear: () => void;
  onQuestionSelect: (index: number) => void;
  onRefreshRoles: () => void;
  onRunCode: () => void;
  onSelectedFocusSkillsChange: (focus: QuestionFocus, skills: string[]) => void;
  onSelectedFocusSkillToggle: (focus: QuestionFocus, skill: string) => void;
  onSelectedRoleChange: (role: string) => void;
  onResumeSession: (sessionId: string) => void;
  onUpdateAnswer: (answer: string) => void;
  onUpdateCode: (code: string) => void;
  onUpdateNote: (note: string) => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  plan: InterviewPlan | null;
  practiceSessions: InterviewPracticeSession[];
  questionFocus: QuestionFocus[];
  questionCount: number;
  preparationLevel: PreparationLevel;
  interviewType: PreparationInterviewType;
  roles: string[];
  selectedRole: string;
  selectedFocusSkills: Partial<Record<QuestionFocus, string[]>>;
  sessionStatus: InterviewPracticeSession['status'];
  skillOptionsStatus: string;
  skillGroups: Partial<Record<QuestionFocus, string[]>>;
}

export function InterviewPracticeView({
  activeSessionId,
  answerRef,
  answerValue,
  answersByQuestion,
  averageScore,
  bookmarked,
  currentEvaluation,
  currentQuestion,
  currentQuestionIndex,
  codeRunResult,
  codeByQuestion,
  codeValue,
  cvTextRef,
  error,
  elapsedSeconds,
  evaluations,
  learningPath,
  loading,
  loadingLabel,
  noteValue,
  onCvBlur,
  onEvaluateAnswer,
  onGeneratePlan,
  onRegenerateQuestion,
  onReportQuestion,
  onRetryQuestion,
  onToggleBookmark,
  onNextQuestion,
  onPauseSession,
  onCompleteSession,
  onPreviousQuestion,
  onQuestionCountChange,
  onPreparationLevelChange,
  onInterviewTypeChange,
  onQuestionFocusClear,
  onQuestionSelect,
  onRefreshRoles,
  onRunCode,
  onSelectedFocusSkillsChange,
  onSelectedFocusSkillToggle,
  onSelectedRoleChange,
  onResumeSession,
  onUpdateAnswer,
  onUpdateCode,
  onUpdateNote,
  onUploadCv,
  plan,
  practiceSessions,
  questionFocus,
  questionCount,
  preparationLevel,
  interviewType,
  roles,
  selectedRole,
  selectedFocusSkills,
  sessionStatus,
  skillOptionsStatus,
  skillGroups,
}: InterviewPracticeViewProps) {
  const [revealedGuidance, setRevealedGuidance] = useState<Set<string>>(new Set());
  const [revealedHints, setRevealedHints] = useState<Set<string>>(new Set());
  const availableSkillFocuses = SKILL_FOCUS_OPTIONS.filter(
    (option) => (skillGroups[option.value]?.length ?? 0) > 0,
  );
  const selectedSkillEntries = Object.entries(selectedFocusSkills).flatMap(([focus, skills]) =>
    (skills ?? []).map((skill) => ({ focus: focus as QuestionFocus, skill })),
  );
  const codingQuestion = currentQuestion ? isCodingQuestion(currentQuestion) : false;
  const completedCount = plan
    ? plan.questions.filter((question) => Boolean(evaluations[question.id])).length
    : 0;
  const guidanceVisible = Boolean(
    currentQuestion && (currentEvaluation || revealedGuidance.has(currentQuestion.id)),
  );

  useEffect(() => {
    setRevealedGuidance(new Set());
  }, [plan]);

  function toggleGuidance(questionId: string) {
    setRevealedGuidance((current) => {
      const next = new Set(current);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  }

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Interview Assistant</p>
          <h1>Practice role-specific interviews and get scored feedback</h1>
        </div>
        <button className="ghost-button" type="button" onClick={onRefreshRoles}>
          Refresh roles
        </button>
      </section>

      {practiceSessions.length > 0 && !plan && (
        <section className="panel table-panel">
          <div className="panel-heading">
            <div>
              <h2>Continue a saved interview</h2>
              <p className="muted-line">Resume exactly where you stopped.</p>
            </div>
          </div>
          <div className="resume-session-grid">
            {practiceSessions.slice(0, 4).map((session) => (
              <button
                className="resume-session"
                key={session.id}
                type="button"
                onClick={() => onResumeSession(session.id)}
              >
                <span>{session.status.replaceAll('_', ' ')}</span>
                <strong>{session.title}</strong>
                <small>{new Date(session.updated_at).toLocaleString()}</small>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="input-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>Candidate CV</h2>
            <label className="file-control">
              <span>Upload</span>
              <input type="file" accept=".txt,.pdf,application/pdf,text/plain" onChange={onUploadCv} />
            </label>
          </div>
          <textarea ref={cvTextRef} spellCheck={false} onBlur={onCvBlur} />
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Interview target</h2>
            <span className="count">{roles.length} saved</span>
          </div>

          <select value={selectedRole} onChange={(event) => onSelectedRoleChange(event.target.value)}>
            <option value="" disabled>
              Select a saved role
            </option>
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <div className="helper-callout">
            Want to practise with a new job role? Upload and save the job description in{' '}
            <Link to="/job-skill-extractor">Job skill extraction</Link>.
          </div>

          <div className="interview-config-grid">
            <label>
              <span className="field-label">Difficulty</span>
              <select value={preparationLevel} onChange={(event) => onPreparationLevelChange(event.target.value as PreparationLevel)}>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
            <label>
              <span className="field-label">Interview type</span>
              <select value={interviewType} onChange={(event) => onInterviewTypeChange(event.target.value as PreparationInterviewType)}>
                <option value="mixed">Mixed</option>
                <option value="technical_theory">Technical theory</option>
                <option value="coding">Coding</option>
                <option value="project">Project experience</option>
                <option value="behavioral">Behavioral</option>
              </select>
            </label>
            <label>
              <span className="field-label">Questions</span>
              <input
                className="number-input"
                min={1}
                max={20}
                type="number"
                value={questionCount}
                onChange={(event) => onQuestionCountChange(Number(event.target.value))}
              />
            </label>
          </div>

          <label className="field-label">Question focus</label>
          <div className="auto-load-note">
            {skillOptionsStatus}
          </div>

          {availableSkillFocuses.length > 0 && (
            <div className="skill-picker">
              {selectedSkillEntries.length > 0 && (
                <div className="selected-skill-row">
                  <span>Selected skills</span>
                  <div className="selected-skill-list">
                    {selectedSkillEntries.map(({ focus, skill }) => (
                      <button
                        className="selected-skill-pill"
                        key={`${focus}-${skill}`}
                        type="button"
                        onClick={() => onSelectedFocusSkillToggle(focus, skill)}
                      >
                        {skill}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {availableSkillFocuses.map((option) => (
                <div className="skill-group-block" key={option.value}>
                  <div className="skill-group-heading">
                    <span className={questionFocus.includes(option.value) ? 'active-skill-label' : ''}>{option.label}</span>
                    {(selectedFocusSkills[option.value]?.length ?? 0) > 0 && (
                      <button type="button" onClick={() => onSelectedFocusSkillsChange(option.value, [])}>
                        Clear
                      </button>
                    )}
                  </div>
                  <select
                    value=""
                    onChange={(event) => {
                      if (event.target.value) {
                        onSelectedFocusSkillToggle(option.value, event.target.value);
                      }
                    }}
                  >
                    <option value="">Select skill</option>
                    {(skillGroups[option.value] ?? [])
                      .filter((skill) => !(selectedFocusSkills[option.value] ?? []).includes(skill))
                      .map((skill) => (
                        <option key={skill} value={skill}>
                          {skill}
                        </option>
                      ))}
                  </select>
                  {(selectedFocusSkills[option.value]?.length ?? 0) > 0 && (
                    <div className="selected-skill-list compact-selected-list">
                      {(selectedFocusSkills[option.value] ?? []).map((skill) => (
                        <button
                          className="selected-skill-pill"
                          key={`${option.value}-${skill}`}
                          type="button"
                          onClick={() => onSelectedFocusSkillToggle(option.value, skill)}
                        >
                          {skill}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <button className="primary-button action-gap" type="button" disabled={loading} onClick={onGeneratePlan}>
            Generate interview plan
          </button>
        </div>
      </section>

      {(loading || error) && (
        <section className="status-row">
          {loading && <div className="status loading">{loadingLabel}...</div>}
          {error && <div className="status error">{error}</div>}
        </section>
      )}

      {plan && (
        <>
          <section className="result-grid">
            <div className="metric-panel">
              <span>Readiness</span>
              <strong>{plan.readiness_score}%</strong>
            </div>
            <div className="metric-panel">
              <span>Questions</span>
              <strong>{plan.questions.length}</strong>
            </div>
            <div className="metric-panel">
              <span>Engine</span>
              <strong className="small-metric">{plan.engine}</strong>
            </div>
            <div className="metric-panel">
              <span>Completed</span>
              <strong>{completedCount}</strong>
            </div>
            <div className="metric-panel">
              <span>Unanswered</span>
              <strong>{plan.questions.length - completedCount}</strong>
            </div>
            <div className="metric-panel">
              <span>Elapsed</span>
              <strong className="small-metric">{formatElapsed(elapsedSeconds)}</strong>
            </div>
          </section>

          <section className="panel table-panel">
            <div className="panel-heading">
              <h2>Practice setup</h2>
              <div className="practice-setup-actions">
                <strong className="score-badge">Average score {averageScore ?? '-'}</strong>
                <button className="ghost-button" type="button" onClick={() => downloadQuestionSetJson(plan)}>
                  Download JSON
                </button>
                <button className="ghost-button" type="button" onClick={() => downloadQuestionSetPdf(plan)}>
                  Download PDF
                </button>
                {sessionStatus !== 'completed' && (
                  <button className="ghost-button" type="button" disabled={!activeSessionId || loading} onClick={onPauseSession}>
                    Pause and save
                  </button>
                )}
                {sessionStatus !== 'completed' && (
                  <button className="primary-button" type="button" disabled={!activeSessionId || loading} onClick={onCompleteSession}>
                    Complete interview
                  </button>
                )}
              </div>
            </div>
            <div className="chips">
              {plan.question_focus.map((focus) => (
                <span key={focus}>{focus.replaceAll('_', ' ')}</span>
              ))}
              {Object.entries(plan.selected_focus_skills ?? {}).flatMap(([focus, skills]) =>
                skills.map((skill) => (
                  <span key={`${focus}-${skill}`}>{skill}</span>
                )),
              )}
              {plan.preparation_level && <span>{plan.preparation_level}</span>}
              {plan.interview_type && <span>{plan.interview_type.replaceAll('_', ' ')}</span>}
            </div>
          </section>

          <section className="practice-grid">
            <div className="panel question-list">
              <h2>Question set</h2>
              {plan.questions.map((question, index) => (
                <button
                  className={index === currentQuestionIndex ? 'question-item active' : 'question-item'}
                  key={question.id}
                  type="button"
                  onClick={() => onQuestionSelect(index)}
                >
                  <span>{index + 1}. {question.question_type}</span>
                  <strong>{evaluations[question.id]?.score ?? '-'}</strong>
                </button>
              ))}
            </div>

            <div className="panel practice-panel">
              {currentQuestion && (
                <>
                  <div className="panel-heading">
                    <div>
                      <h2>Question {currentQuestionIndex + 1}</h2>
                      <p className="muted-line">{currentQuestion.question_type} · {currentQuestion.difficulty}</p>
                    </div>
                    <div className="question-tools">
                      {currentQuestion.skill && <span className="skill-pill">{currentQuestion.skill}</span>}
                      <button className="ghost-button" type="button" onClick={onToggleBookmark}>
                        {bookmarked ? 'Bookmarked' : 'Bookmark'}
                      </button>
                      <button className="ghost-button" type="button" disabled={loading} onClick={onRegenerateQuestion}>
                        Regenerate
                      </button>
                    </div>
                  </div>

                  <p className="question-text">{currentQuestion.question}</p>
                  <div className="question-quality-actions">
                    <button type="button" onClick={() => onReportQuestion('irrelevant')}>Report irrelevant</button>
                    <button type="button" onClick={() => onReportQuestion('poor_quality')}>Report poor quality</button>
                    {currentQuestion.hint && (
                      <button
                        type="button"
                        onClick={() => setRevealedHints((current) => new Set(current).add(currentQuestion.id))}
                      >
                        Show hint
                      </button>
                    )}
                  </div>
                  {revealedHints.has(currentQuestion.id) && <p className="hint-callout">{currentQuestion.hint}</p>}

                  <div className="guidance-control">
                    <div>
                      <strong>Expected points and rubric</strong>
                      <span>
                        {currentQuestion.criteria_source === 'template'
                          ? 'Reviewed Python topic criteria'
                          : 'Question-specific criteria'}
                      </span>
                    </div>
                    {!currentEvaluation && (
                      <button className="ghost-button" type="button" onClick={() => toggleGuidance(currentQuestion.id)}>
                        {guidanceVisible ? 'Hide guidance' : 'Reveal guidance'}
                      </button>
                    )}
                  </div>

                  {guidanceVisible && (
                    <div className="lists compact-lists guidance-content">
                      <div>
                        <h3>Expected points</h3>
                        <ul>
                          {currentQuestion.expected_points.map((point, index) => (
                            <li key={point}>
                              {point}
                              <strong className="point-weight">
                                {currentQuestion.expected_point_weights?.[index] ?? '-'} pts
                              </strong>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h3>Rubric</h3>
                        <ul>
                          {currentQuestion.scoring_rubric.map((point) => (
                            <li key={point}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {codingQuestion && (
                    <div className="code-runner">
                      <textarea
                        className="code-textarea"
                        spellCheck={false}
                        value={codeValue}
                        onChange={(event) => onUpdateCode(event.target.value)}
                      />
                      <button className="ghost-button full-width" type="button" disabled={loading} onClick={onRunCode}>
                        Run Python code
                      </button>
                      {error && <div className="status error code-run-error">{error}</div>}
                      {codeRunResult && (
                        <div className="code-output">
                          <div>
                            <h3>Output</h3>
                            <pre>{codeRunResult.stdout || '-'}</pre>
                          </div>
                          <div>
                            <h3>Error</h3>
                            <pre>{codeRunResult.stderr || '-'}</pre>
                          </div>
                          <strong>Exit code {codeRunResult.exit_code ?? '-'}</strong>
                          {codeRunResult.timed_out && <strong>Timed out</strong>}
                        </div>
                      )}
                    </div>
                  )}

                  <textarea
                    className="answer-textarea"
                    ref={answerRef}
                    spellCheck={false}
                    value={answerValue}
                    onChange={(event) => onUpdateAnswer(event.target.value)}
                  />
                  <label className="question-notes">
                    <span>Private notes</span>
                    <textarea
                      className="short-textarea"
                      value={noteValue}
                      onChange={(event) => onUpdateNote(event.target.value)}
                    />
                  </label>
                  <button className="primary-button" type="button" disabled={loading || sessionStatus === 'completed'} onClick={onEvaluateAnswer}>
                    Score answer
                  </button>

                  <div className="navigation-row">
                    <button className="ghost-button" type="button" disabled={currentQuestionIndex === 0} onClick={onPreviousQuestion}>
                      Previous
                    </button>
                    <button className="ghost-button" type="button" disabled={currentQuestionIndex === plan.questions.length - 1} onClick={onNextQuestion}>
                      Next
                    </button>
                  </div>
                </>
              )}
            </div>
          </section>
        </>
      )}

      {currentEvaluation && (
        <>
          <section className="panel table-panel score-explanation">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Score explanation</p>
                <h2>How your {currentEvaluation.score}/10 score was calculated</h2>
              </div>
            </div>
            <div className="score-breakdown-grid">
              {(currentEvaluation.score_breakdown ?? []).map((item) => (
                <article key={item.category}>
                  <div>
                    <strong>{item.label}</strong>
                    <span>{item.awarded_score}/{item.max_score}</span>
                  </div>
                  <progress max={item.max_score || 1} value={item.awarded_score} />
                  <p>{item.explanation}</p>
                </article>
              ))}
            </div>
            <h3>Expected-point assessment</h3>
            <div className="point-assessment-list">
              {(currentEvaluation.expected_point_assessments ?? []).map((item) => (
                <article key={item.point}>
                  <div>
                    <strong>{item.point}</strong>
                    <span>{item.awarded_score}/{item.weight}</span>
                  </div>
                  <p>{item.explanation}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="detail-grid">
            <div className="panel">
            <div className="panel-heading">
              <h2>Answer feedback</h2>
              <strong className="score-badge">{currentEvaluation.score}/10 · {currentEvaluation.rating}</strong>
            </div>
            <p>{currentEvaluation.feedback}</p>
            <div className="lists compact-lists">
              <div>
                <h3>Strengths</h3>
                <ul>
                  {currentEvaluation.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3>Weaknesses</h3>
                <ul>
                  {currentEvaluation.weaknesses.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            </div>

            <div className="panel">
              <h2>Improved answer outline</h2>
              <ul>
                {currentEvaluation.improved_answer_outline.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              {currentEvaluation.follow_up_question && (
                <>
                  <h3>Follow-up question</h3>
                  <p>{currentEvaluation.follow_up_question}</p>
                </>
              )}
              <button className="ghost-button full-width" type="button" onClick={onRetryQuestion}>
                Retry this question
              </button>
            </div>
          </section>
        </>
      )}

      {learningPath.length > 0 && (
        <section className="panel table-panel">
          <h2>Learning path</h2>
          <div className="learning-grid">
            {learningPath.map((item) => (
              <article className="learning-item" key={`${item.priority}-${item.topic}`}>
                <span>{item.priority}</span>
                <h3>{item.topic}</h3>
                <p>{item.why_it_matters}</p>
                <strong>{item.estimated_time}</strong>
                <ul>
                  {item.practice_tasks.slice(0, 2).map((task) => (
                    <li key={task}>{task}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      )}

      {plan && sessionStatus === 'completed' && (
        <section className="panel table-panel final-report">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Final interview report</p>
              <h2>{plan.role}</h2>
            </div>
            <button
              className="primary-button"
              type="button"
              onClick={() => downloadInterviewReportPdf(plan, answersByQuestion, codeByQuestion, evaluations, learningPath)}
            >
              Download complete report PDF
            </button>
          </div>
          <div className="report-summary">
            <div><span>Average score</span><strong>{averageScore ?? '-'}/10</strong></div>
            <div><span>Completed</span><strong>{completedCount}/{plan.questions.length}</strong></div>
            <div><span>Learning topics</span><strong>{learningPath.length}</strong></div>
          </div>
          <div className="report-question-list">
            {plan.questions.map((question, index) => (
              <article key={question.id}>
                <span>Question {index + 1} · {question.skill ?? question.question_type}</span>
                <h3>{question.question}</h3>
                <p>{evaluations[question.id]?.feedback ?? 'Not answered'}</p>
                <strong>{evaluations[question.id]?.score ?? '-'}/10</strong>
              </article>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

const SKILL_FOCUS_OPTIONS: { label: string; value: QuestionFocus }[] = [
  { label: 'Matched strongly required', value: 'matched_strongly_required' },
  { label: 'Matched skills', value: 'matched_skills' },
  { label: 'Matched required', value: 'matched_required' },
  { label: 'Missing strongly required', value: 'missing_strongly_required' },
  { label: 'Missing skills', value: 'missing_skills' },
  { label: 'Missing required', value: 'missing_required' },
  { label: 'Matched tools', value: 'matched_tools' },
  { label: 'Missing tools', value: 'missing_tools' },
  { label: 'Soft skills', value: 'soft_skills' },
  { label: 'Responsibilities', value: 'responsibilities' },
];

function isCodingQuestion(question: InterviewQuestion) {
  return question.is_coding;
}

function downloadQuestionSetJson(plan: InterviewPlan) {
  const payload = {
    role: plan.role,
    preparation_level: plan.preparation_level,
    interview_type: plan.interview_type,
    selected_focus_skills: plan.selected_focus_skills,
    questions: plan.questions.map(candidateQuestion),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${questionSetFilename(plan)}-questions.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function downloadQuestionSetPdf(plan: InterviewPlan) {
  const document = new jsPDF({ unit: 'pt', format: 'a4' });
  const left = 48;
  const width = document.internal.pageSize.getWidth() - left * 2;
  const pageBottom = document.internal.pageSize.getHeight() - 48;
  let y = 52;

  function write(text: string, options: { bold?: boolean; size?: number; gap?: number } = {}) {
    const size = options.size ?? 10;
    const gap = options.gap ?? 6;
    document.setFont('helvetica', options.bold ? 'bold' : 'normal');
    document.setFontSize(size);
    const lines = document.splitTextToSize(text, width) as string[];
    const lineHeight = size * 1.35;
    if (y + lines.length * lineHeight > pageBottom) {
      document.addPage();
      y = 52;
    }
    document.text(lines, left, y);
    y += lines.length * lineHeight + gap;
  }

  write(`${plan.role} Interview Questions`, { bold: true, size: 18, gap: 10 });
  write(`Difficulty: ${plan.preparation_level ?? 'Not specified'} | Type: ${(plan.interview_type ?? 'Not specified').replaceAll('_', ' ')}`, { gap: 16 });

  plan.questions.forEach((question, index) => {
    write(`${index + 1}. ${question.question}`, { bold: true, size: 12, gap: 4 });
    write(`Skill: ${question.skill ?? 'Not specified'} | ${question.question_type} | ${question.difficulty}`, { gap: 8 });
    y += 12;
  });

  document.save(`${questionSetFilename(plan)}-questions.pdf`);
}

function questionSetFilename(plan: InterviewPlan) {
  return plan.role.toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'interview';
}

function candidateQuestion(question: InterviewQuestion) {
  return {
    id: question.id,
    question: question.question,
    question_type: question.question_type,
    difficulty: question.difficulty,
    skill: question.skill,
    is_coding: question.is_coding,
  };
}

function formatElapsed(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${remainder.toString().padStart(2, '0')}`;
}

function downloadInterviewReportPdf(
  plan: InterviewPlan,
  answersByQuestion: Record<string, string>,
  codeByQuestion: Record<string, string>,
  evaluations: Record<string, AnswerEvaluation>,
  learningPath: LearningPathItem[],
) {
  const document = new jsPDF({ unit: 'pt', format: 'a4' });
  const left = 48;
  const width = document.internal.pageSize.getWidth() - left * 2;
  const pageBottom = document.internal.pageSize.getHeight() - 48;
  const scores = Object.values(evaluations).map((evaluation) => evaluation.score);
  const average = scores.length
    ? Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 10) / 10
    : 0;
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

  write(`${plan.role} Interview Report`, { bold: true, size: 18, gap: 10 });
  write(`Average score: ${average}/10 | Answered: ${scores.length}/${plan.questions.length}`, { gap: 18 });

  plan.questions.forEach((question, index) => {
    const evaluation = evaluations[question.id];
    write(`${index + 1}. ${question.question}`, { bold: true, size: 12, gap: 4 });
    write(`Skill: ${question.skill ?? '-'} | Score: ${evaluation?.score ?? '-'}/10`, { gap: 8 });
    write('Written answer', { bold: true, gap: 2 });
    write(answersByQuestion[question.id] || 'Not answered', { gap: 8 });
    if (codeByQuestion[question.id]) {
      write('Submitted code', { bold: true, gap: 2 });
      write(codeByQuestion[question.id], { gap: 8 });
    }
    write('Feedback', { bold: true, gap: 2 });
    write(evaluation?.feedback ?? 'Not scored', { gap: 12 });
  });

  if (learningPath.length) {
    write('Learning Path', { bold: true, size: 15, gap: 8 });
    learningPath.forEach((item) => {
      write(`${item.topic} (${item.priority})`, { bold: true, gap: 2 });
      item.practice_tasks.forEach((task) => write(`- ${task}`, { gap: 2 }));
      y += 6;
    });
  }

  document.save(`${questionSetFilename(plan)}-interview-report.pdf`);
}
