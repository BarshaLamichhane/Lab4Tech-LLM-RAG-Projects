import { ChangeEvent, RefObject } from 'react';
import { Link } from 'react-router-dom';

import type {
  AnswerEvaluation,
  CodeRunResponse,
  InterviewPlan,
  InterviewQuestion,
  LearningPathItem,
  QuestionFocus,
} from '../types';

interface InterviewPracticeViewProps {
  answerRef: RefObject<HTMLTextAreaElement | null>;
  averageScore: number | null;
  currentEvaluation: AnswerEvaluation | null;
  currentQuestion: InterviewQuestion | null;
  currentQuestionIndex: number;
  codeRunResult: CodeRunResponse | null;
  codeValue: string;
  cvTextRef: RefObject<HTMLTextAreaElement | null>;
  error: string;
  evaluations: Record<string, AnswerEvaluation>;
  learningPath: LearningPathItem[];
  loading: boolean;
  loadingLabel: string;
  onCvBlur: () => void;
  onEvaluateAnswer: () => void;
  onGeneratePlan: () => void;
  onNextQuestion: () => void;
  onPreviousQuestion: () => void;
  onQuestionCountChange: (count: number) => void;
  onQuestionFocusClear: () => void;
  onQuestionSelect: (index: number) => void;
  onRefreshRoles: () => void;
  onRunCode: () => void;
  onSelectedFocusSkillsChange: (focus: QuestionFocus, skills: string[]) => void;
  onSelectedFocusSkillToggle: (focus: QuestionFocus, skill: string) => void;
  onSelectedRoleChange: (role: string) => void;
  onUpdateCode: (code: string) => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  plan: InterviewPlan | null;
  questionFocus: QuestionFocus[];
  questionCount: number;
  roles: string[];
  selectedRole: string;
  selectedFocusSkills: Partial<Record<QuestionFocus, string[]>>;
  skillOptionsStatus: string;
  skillGroups: Partial<Record<QuestionFocus, string[]>>;
}

export function InterviewPracticeView({
  answerRef,
  averageScore,
  currentEvaluation,
  currentQuestion,
  currentQuestionIndex,
  codeRunResult,
  codeValue,
  cvTextRef,
  error,
  evaluations,
  learningPath,
  loading,
  loadingLabel,
  onCvBlur,
  onEvaluateAnswer,
  onGeneratePlan,
  onNextQuestion,
  onPreviousQuestion,
  onQuestionCountChange,
  onQuestionFocusClear,
  onQuestionSelect,
  onRefreshRoles,
  onRunCode,
  onSelectedFocusSkillsChange,
  onSelectedFocusSkillToggle,
  onSelectedRoleChange,
  onUpdateCode,
  onUploadCv,
  plan,
  questionFocus,
  questionCount,
  roles,
  selectedRole,
  selectedFocusSkills,
  skillOptionsStatus,
  skillGroups,
}: InterviewPracticeViewProps) {
  const availableSkillFocuses = SKILL_FOCUS_OPTIONS.filter(
    (option) => (skillGroups[option.value]?.length ?? 0) > 0,
  );
  const selectedSkillEntries = Object.entries(selectedFocusSkills).flatMap(([focus, skills]) =>
    (skills ?? []).map((skill) => ({ focus: focus as QuestionFocus, skill })),
  );
  const codingQuestion = currentQuestion ? isCodingQuestion(currentQuestion) : false;

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

          <label className="field-label" htmlFor="question-count">Questions</label>
          <input
            id="question-count"
            className="number-input"
            min={5}
            max={20}
            type="number"
            value={questionCount}
            onChange={(event) => onQuestionCountChange(Number(event.target.value))}
          />

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
          </section>

          <section className="panel table-panel">
            <div className="panel-heading">
              <h2>Practice setup</h2>
              <strong className="score-badge">Average score {averageScore ?? '-'}</strong>
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
                    {currentQuestion.skill && <span className="skill-pill">{currentQuestion.skill}</span>}
                  </div>

                  <p className="question-text">{currentQuestion.question}</p>

                  <div className="lists compact-lists">
                    <div>
                      <h3>Expected points</h3>
                      <ul>
                        {currentQuestion.expected_points.map((point) => (
                          <li key={point}>{point}</li>
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

                  <textarea className="answer-textarea" ref={answerRef} spellCheck={false} />
                  <button className="primary-button" type="button" disabled={loading} onClick={onEvaluateAnswer}>
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
          </div>
        </section>
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
  const text = [
    question.question,
    question.skill ?? '',
    ...question.expected_points,
    ...question.scoring_rubric,
  ].join(' ').toLowerCase();

  return (
    text.includes('python') &&
    (
      text.includes('write') ||
      text.includes('function') ||
      text.includes('class') ||
      text.includes('code') ||
      text.includes('implement') ||
      text.includes('list comprehension')
    )
  );
}
