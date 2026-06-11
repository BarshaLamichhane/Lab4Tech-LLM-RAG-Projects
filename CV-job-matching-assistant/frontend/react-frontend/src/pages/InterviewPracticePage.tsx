import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';

import {
  buildInterviewContext,
  buildLearningPath,
  createInterviewSession,
  evaluateInterviewAnswer,
  generatePreparationInterview,
  getInterviewSessions,
  getRoles,
  regeneratePreparationQuestion,
  reportInterviewQuestion,
  runPythonCode,
  updateInterviewSession,
  uploadText,
} from '../api';
import type {
  AnswerEvaluation,
  BuildInterviewPlanResponse,
  CodeRunResponse,
  InterviewContext,
  InterviewPracticeSession,
  InterviewPracticeSessionPayload,
  InterviewQuestion,
  LearningPathItem,
  PreparationInterviewType,
  PreparationLevel,
  QuestionFocus,
} from '../types';
import { errorMessage } from '../ui';
import { InterviewPracticeView } from './InterviewPracticeView';

export function InterviewPracticePage() {
  const cvTextRef = useRef<HTMLTextAreaElement>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [questionFocus, setQuestionFocus] = useState<QuestionFocus[]>(['all']);
  const [selectedFocusSkills, setSelectedFocusSkills] = useState<Partial<Record<QuestionFocus, string[]>>>({});
  const [questionCount, setQuestionCount] = useState(10);
  const [preparationLevel, setPreparationLevel] = useState<PreparationLevel>('intermediate');
  const [interviewType, setInterviewType] = useState<PreparationInterviewType>('mixed');
  const [interviewContext, setInterviewContext] = useState<InterviewContext | null>(null);
  const [planResponse, setPlanResponse] = useState<BuildInterviewPlanResponse | null>(null);
  const [practiceSessions, setPracticeSessions] = useState<InterviewPracticeSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState('');
  const [sessionStatus, setSessionStatus] = useState<InterviewPracticeSession['status']>('in_progress');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answersByQuestion, setAnswersByQuestion] = useState<Record<string, string>>({});
  const [evaluations, setEvaluations] = useState<Record<string, AnswerEvaluation>>({});
  const [codeByQuestion, setCodeByQuestion] = useState<Record<string, string>>({});
  const [notesByQuestion, setNotesByQuestion] = useState<Record<string, string>>({});
  const [bookmarkedQuestionIds, setBookmarkedQuestionIds] = useState<string[]>([]);
  const [retryCounts, setRetryCounts] = useState<Record<string, number>>({});
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [codeRunResult, setCodeRunResult] = useState<CodeRunResponse | null>(null);
  const [learningPath, setLearningPath] = useState<LearningPathItem[]>([]);
  const [loadingLabel, setLoadingLabel] = useState('');
  const [skillOptionsStatus, setSkillOptionsStatus] = useState('Upload a CV and choose a saved role to load skill options.');
  const [loadedSkillOptionsKey, setLoadedSkillOptionsKey] = useState('');
  const [error, setError] = useState('');

  const loading = Boolean(loadingLabel);
  const questions = planResponse?.interview_plan.questions ?? [];
  const currentQuestion: InterviewQuestion | null = questions[currentQuestionIndex] ?? null;
  const currentEvaluation = currentQuestion ? evaluations[currentQuestion.id] ?? null : null;

  const averageScore = useMemo(() => {
    const scores = Object.values(evaluations).map((evaluation) => evaluation.score);
    if (!scores.length) {
      return null;
    }
    return Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 10) / 10;
  }, [evaluations]);

  useEffect(() => {
    refreshRoles();
    refreshPracticeSessions();
  }, []);

  useEffect(() => {
    if (!activeSessionId || !planResponse || sessionStatus === 'completed') {
      return;
    }
    const timeout = window.setTimeout(() => {
      persistSession(sessionStatus).catch((caughtError) => setError(errorMessage(caughtError)));
    }, 1000);
    return () => window.clearTimeout(timeout);
  }, [
    activeSessionId,
    answersByQuestion,
    codeByQuestion,
    currentQuestionIndex,
    evaluations,
    learningPath,
    planResponse,
    notesByQuestion,
    bookmarkedQuestionIds,
    retryCounts,
    sessionStatus,
  ]);

  useEffect(() => {
    if (!planResponse || sessionStatus !== 'in_progress') return;
    const interval = window.setInterval(() => setElapsedSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(interval);
  }, [planResponse, sessionStatus]);

  async function refreshRoles() {
    try {
      const loadedRoles = await getRoles();
      setRoles(loadedRoles);
      setSelectedRole((currentRole) => currentRole || loadedRoles[0] || '');
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  async function refreshPracticeSessions() {
    try {
      setPracticeSessions(await getInterviewSessions());
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  async function uploadCv(event: ChangeEvent<HTMLInputElement>) {
    await uploadFileText(event);
  }

  async function handleCvBlur() {
    await loadSkillOptionsForRole(selectedRole);
  }

  async function handleSelectedRoleChange(role: string) {
    setSelectedRole(role);
    setInterviewContext(null);
    setSelectedFocusSkills({});
    setQuestionFocus(['all']);
    setPlanResponse(null);
    setActiveSessionId('');
    setSessionStatus('in_progress');
    setAnswersByQuestion({});
    setLearningPath([]);
    setEvaluations({});
    setCodeByQuestion({});
    setNotesByQuestion({});
    setBookmarkedQuestionIds([]);
    setRetryCounts({});
    setElapsedSeconds(0);
    setCodeRunResult(null);
    setLoadedSkillOptionsKey('');
    await loadSkillOptionsForRole(role);
  }

  async function generatePlan() {
    const inputs = getInterviewInputs();
    if (!inputs) {
      return;
    }

    await runTask('Generating interview plan', async () => {
      const resolvedQuestionFocus = questionFocusFromSelectedSkills(selectedFocusSkills);
      const selectedSkills = selectedSkillsFromFocusMap(selectedFocusSkills);
      if (!selectedSkills.length) {
        setError('Select at least one skill before generating preparation questions.');
        return;
      }

      const role = inputs.targetRole ?? interviewContextRole() ?? 'Target role';
      const candidateProjects = Array.isArray(interviewContext?.candidate_profile.projects)
        ? interviewContext.candidate_profile.projects as Record<string, unknown>[]
        : [];
      const preparationResponse = await generatePreparationInterview(
        role,
        selectedSkills,
        candidateProjects,
        questionCount,
        preparationLevel,
        interviewType,
      );
      const context = interviewContext ?? {
        candidate_profile: {},
        job_profile: { role },
        match_result: { score: 0 },
        focus_skills: selectedSkills,
        gap_skills: [],
        skill_groups: {},
      };
      const nextPlanResponse: BuildInterviewPlanResponse = {
        context,
        interview_plan: {
          role: preparationResponse.role,
          readiness_score: Number(context.match_result?.score ?? 0),
          engine: 'mistral',
          question_focus: resolvedQuestionFocus,
          selected_focus_skills: selectedFocusSkills,
          interview_rounds: ['Preparation question set'],
          questions: preparationResponse.questions,
          learning_path: [],
          preparation_level: preparationResponse.level,
          interview_type: preparationResponse.interview_type,
        },
      };
      setPlanResponse(nextPlanResponse);
      setLearningPath([]);
      setEvaluations({});
      setAnswersByQuestion({});
      setCodeByQuestion({});
      setNotesByQuestion({});
      setBookmarkedQuestionIds([]);
      setRetryCounts({});
      setElapsedSeconds(0);
      setCodeRunResult(null);
      setCurrentQuestionIndex(0);
      if (answerRef.current) {
        answerRef.current.value = '';
      }
      const session = await createInterviewSession(
        `${preparationResponse.role} interview practice`,
        buildSessionPayload(nextPlanResponse, {}, {}, {}, [], 0, {}, [], {}, 0),
      );
      setActiveSessionId(session.id);
      setSessionStatus(session.status);
      await refreshPracticeSessions();
    });
  }

  async function loadSkillOptionsForRole(role: string) {
    const cvText = cvTextRef.current?.value.trim() ?? '';
    if (!role) {
      setSkillOptionsStatus('Choose a saved role to load skill options.');
      return;
    }
    if (!cvText) {
      setSkillOptionsStatus('Upload or paste a CV, then skill options will load automatically.');
      return;
    }

    const nextKey = `${role}:${cvText.length}`;
    if (nextKey === loadedSkillOptionsKey) {
      return;
    }

    await runTask('Loading skill options', async () => {
      const context = await buildInterviewContext(cvText, {
        targetRole: role,
      });
      setInterviewContext(context);
      setSelectedFocusSkills({});
      setQuestionFocus(['all']);
      setLoadedSkillOptionsKey(nextKey);
      setSkillOptionsStatus('CV and job role skills compared and loaded. Now choose what you want to practise for interview.');
    });
  }

  async function evaluateCurrentAnswer() {
    if (!planResponse || !currentQuestion) {
      return;
    }

    const writtenAnswer = answersByQuestion[currentQuestion.id]?.trim() ?? '';
    const code = codeByQuestion[currentQuestion.id]?.trim() ?? '';
    const codingQuestion = isCodingQuestion(currentQuestion);

    if (!writtenAnswer && (!codingQuestion || !code)) {
      setError('Write an answer before scoring it.');
      return;
    }

    await runTask('Scoring answer', async () => {
      let runResult = codeRunResult;
      if (codingQuestion && code) {
        runResult = await runPythonCode(code);
        setCodeRunResult(runResult);
      }

      const answerForScoring = codingQuestion && code
        ? buildCodingAnswerForScoring(code, runResult, writtenAnswer)
        : writtenAnswer;
      const evaluation = await evaluateInterviewAnswer(currentQuestion, answerForScoring, planResponse.context, 'mistral');
      const nextEvaluations = {
        ...evaluations,
        [currentQuestion.id]: evaluation,
      };
      setEvaluations(nextEvaluations);
      const updatedLearningPath = await buildLearningPath(planResponse.context, Object.values(nextEvaluations));
      setLearningPath(updatedLearningPath);
    });
  }

  function goToQuestion(index: number) {
    setCurrentQuestionIndex(index);
    setError('');
    setCodeRunResult(null);
  }

  function goToNextQuestion() {
    goToQuestion(Math.min(currentQuestionIndex + 1, questions.length - 1));
  }

  function goToPreviousQuestion() {
    goToQuestion(Math.max(currentQuestionIndex - 1, 0));
  }

  async function runCurrentCode() {
    if (!currentQuestion) {
      return;
    }

    const code = codeByQuestion[currentQuestion.id]?.trim() ?? '';
    if (!code) {
      setError('Write Python code before running it.');
      return;
    }

    await runTask('Running code', async () => {
      const result = await runPythonCode(code);
      setCodeRunResult(result);
    });
  }

  function updateCurrentCode(code: string) {
    if (!currentQuestion) {
      return;
    }
    setCodeByQuestion((currentCode) => ({
      ...currentCode,
      [currentQuestion.id]: code,
    }));
  }

  function updateCurrentAnswer(answer: string) {
    if (!currentQuestion) {
      return;
    }
    setAnswersByQuestion((currentAnswers) => ({
      ...currentAnswers,
      [currentQuestion.id]: answer,
    }));
  }

  function updateCurrentNote(note: string) {
    if (!currentQuestion) return;
    setNotesByQuestion((current) => ({ ...current, [currentQuestion.id]: note }));
  }

  function toggleCurrentBookmark() {
    if (!currentQuestion) return;
    setBookmarkedQuestionIds((current) =>
      current.includes(currentQuestion.id)
        ? current.filter((id) => id !== currentQuestion.id)
        : [...current, currentQuestion.id],
    );
  }

  function retryCurrentQuestion() {
    if (!currentQuestion) return;
    setEvaluations((current) => {
      const next = { ...current };
      delete next[currentQuestion.id];
      return next;
    });
    setRetryCounts((current) => ({
      ...current,
      [currentQuestion.id]: (current[currentQuestion.id] ?? 0) + 1,
    }));
    setCodeRunResult(null);
  }

  async function regenerateCurrentQuestion() {
    if (!planResponse || !currentQuestion) return;
    await runTask('Regenerating question', async () => {
      const candidateProjects = Array.isArray(planResponse.context.candidate_profile.projects)
        ? planResponse.context.candidate_profile.projects as Record<string, unknown>[]
        : [];
      const replacement = await regeneratePreparationQuestion(
        planResponse.interview_plan.role,
        selectedSkillsFromFocusMap(planResponse.interview_plan.selected_focus_skills),
        candidateProjects,
        planResponse.interview_plan.preparation_level ?? 'intermediate',
        planResponse.interview_plan.interview_type ?? 'mixed',
        currentQuestion.id,
        planResponse.interview_plan.questions,
      );
      setPlanResponse({
        ...planResponse,
        interview_plan: {
          ...planResponse.interview_plan,
          questions: planResponse.interview_plan.questions.map((question) =>
            question.id === currentQuestion.id ? replacement : question
          ),
        },
      });
      retryCurrentQuestion();
      setAnswersByQuestion((current) => ({ ...current, [currentQuestion.id]: '' }));
      setCodeByQuestion((current) => ({ ...current, [currentQuestion.id]: '' }));
    });
  }

  async function reportCurrentQuestion(reason: 'irrelevant' | 'poor_quality') {
    if (!currentQuestion) return;
    await runTask('Reporting question', async () => {
      await reportInterviewQuestion(currentQuestion, reason);
    });
  }

  async function pauseSession() {
    await runTask('Saving interview session', async () => {
      await persistSession('paused');
      setSessionStatus('paused');
      await refreshPracticeSessions();
    });
  }

  async function completeSession() {
    await runTask('Completing interview session', async () => {
      await persistSession('completed');
      setSessionStatus('completed');
      await refreshPracticeSessions();
    });
  }

  async function resumeSession(sessionId: string) {
    const session = practiceSessions.find((item) => item.id === sessionId);
    if (!session) {
      return;
    }
    const payload = session.payload;
    setPlanResponse(payload.plan_response);
    setSelectedRole(payload.plan_response.interview_plan.role);
    setInterviewContext(payload.plan_response.context);
    setSelectedFocusSkills(payload.plan_response.interview_plan.selected_focus_skills ?? {});
    setQuestionFocus(payload.plan_response.interview_plan.question_focus ?? ['all']);
    setPreparationLevel(payload.plan_response.interview_plan.preparation_level ?? 'intermediate');
    setInterviewType(payload.plan_response.interview_plan.interview_type ?? 'mixed');
    setQuestionCount(payload.plan_response.interview_plan.questions.length);
    setAnswersByQuestion(payload.answers_by_question ?? {});
    setCodeByQuestion(payload.code_by_question ?? {});
    setEvaluations(payload.evaluations ?? {});
    setLearningPath(payload.learning_path ?? []);
    setNotesByQuestion(payload.notes_by_question ?? {});
    setBookmarkedQuestionIds(payload.bookmarked_question_ids ?? []);
    setRetryCounts(payload.retry_counts ?? {});
    setElapsedSeconds(payload.elapsed_seconds ?? 0);
    setCurrentQuestionIndex(payload.current_question_index ?? 0);
    setActiveSessionId(session.id);
    setSessionStatus(session.status === 'completed' ? 'completed' : 'in_progress');
    setCodeRunResult(null);
    if (session.status !== 'completed') {
      await updateInterviewSession(session.id, session.title, 'in_progress', payload);
    }
  }

  async function persistSession(status: InterviewPracticeSession['status']) {
    if (!activeSessionId || !planResponse) {
      return;
    }
    await updateInterviewSession(
      activeSessionId,
      `${planResponse.interview_plan.role} interview practice`,
      status,
      buildSessionPayload(
        planResponse,
        answersByQuestion,
        codeByQuestion,
        evaluations,
        learningPath,
        currentQuestionIndex,
        notesByQuestion,
        bookmarkedQuestionIds,
        retryCounts,
        elapsedSeconds,
      ),
    );
  }

  function updateQuestionFocusFromSelections(nextSkills: Partial<Record<QuestionFocus, string[]>>) {
    setQuestionFocus(questionFocusFromSelectedSkills(nextSkills));
  }

  function clearQuestionFocus() {
      setQuestionFocus(['all']);
      setSelectedFocusSkills({});
  }

  function questionFocusFromSelectedSkills(nextSkills: Partial<Record<QuestionFocus, string[]>>) {
    const selectedFocuses = Object.entries(nextSkills)
      .filter(([focus, skills]) => focus !== 'all' && (skills?.length ?? 0) > 0)
      .map(([focus]) => focus as QuestionFocus);
    return selectedFocuses.length ? selectedFocuses : (['all'] as QuestionFocus[]);
  }

  function selectedSkillsFromFocusMap(nextSkills: Partial<Record<QuestionFocus, string[]>>) {
    return Object.values(nextSkills).flatMap((skills) => skills ?? []);
  }

  function buildCodingAnswerForScoring(
    code: string,
    runResult: CodeRunResponse | null,
    writtenAnswer: string,
  ) {
    return [
      'Candidate submitted Python code:',
      '```python',
      code,
      '```',
      '',
      'Runtime result:',
      `stdout: ${runResult?.stdout || '-'}`,
      `stderr: ${runResult?.stderr || '-'}`,
      `exit_code: ${runResult?.exit_code ?? '-'}`,
      `timed_out: ${runResult?.timed_out ? 'yes' : 'no'}`,
      '',
      'Candidate explanation:',
      writtenAnswer || '-',
    ].join('\n');
  }

  function isCodingQuestion(question: InterviewQuestion) {
    return question.is_coding;
  }

  function interviewContextRole() {
    const role = interviewContext?.job_profile?.role;
    return typeof role === 'string' ? role : null;
  }

  function updateSelectedFocusSkills(focus: QuestionFocus, skills: string[]) {
    if (focus === 'all') {
      return;
    }
    setSelectedFocusSkills((currentSkills) => {
      const nextSkills = { ...currentSkills };
      if (skills.length) {
        nextSkills[focus] = skills;
      } else {
        delete nextSkills[focus];
      }
      updateQuestionFocusFromSelections(nextSkills);
      return nextSkills;
    });
  }

  function toggleSelectedFocusSkill(focus: QuestionFocus, skill: string) {
    if (focus === 'all') {
      return;
    }

    const currentSkills = selectedFocusSkills[focus] ?? [];
    const nextSkills = currentSkills.includes(skill)
      ? currentSkills.filter((currentSkill) => currentSkill !== skill)
      : [...currentSkills, skill];
    updateSelectedFocusSkills(focus, nextSkills);
  }

  function getInterviewInputs() {
    const cvText = cvTextRef.current?.value.trim() ?? '';

    if (!cvText) {
      setError('Add a CV before continuing.');
      return null;
    }
    if (!selectedRole) {
      setError('Choose a saved target role.');
      return null;
    }

    return {
      cvText,
      targetRole: selectedRole,
    };
  }

  async function uploadFileText(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    await runTask('Reading CV file', async () => {
      const text = await uploadText(file, 'cv');
      if (cvTextRef.current) {
        cvTextRef.current.value = text;
      }
    });
    await loadSkillOptionsForRole(selectedRole);
  }

  async function runTask(label: string, task: () => Promise<void>) {
    setError('');
    setLoadingLabel(label);
    try {
      await task();
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    } finally {
      setLoadingLabel('');
    }
  }

  return (
    <InterviewPracticeView
      answerRef={answerRef}
      answerValue={currentQuestion ? answersByQuestion[currentQuestion.id] ?? '' : ''}
      answersByQuestion={answersByQuestion}
      averageScore={averageScore}
      currentEvaluation={currentEvaluation}
      currentQuestion={currentQuestion}
      currentQuestionIndex={currentQuestionIndex}
      codeRunResult={codeRunResult}
      codeByQuestion={codeByQuestion}
      codeValue={currentQuestion ? codeByQuestion[currentQuestion.id] ?? '' : ''}
      noteValue={currentQuestion ? notesByQuestion[currentQuestion.id] ?? '' : ''}
      bookmarked={currentQuestion ? bookmarkedQuestionIds.includes(currentQuestion.id) : false}
      elapsedSeconds={elapsedSeconds}
      cvTextRef={cvTextRef}
      error={error}
      evaluations={evaluations}
      learningPath={learningPath}
      loading={loading}
      loadingLabel={loadingLabel}
      activeSessionId={activeSessionId}
      sessionStatus={sessionStatus}
      practiceSessions={practiceSessions}
      onCvBlur={handleCvBlur}
      onEvaluateAnswer={evaluateCurrentAnswer}
      onGeneratePlan={generatePlan}
      onRegenerateQuestion={regenerateCurrentQuestion}
      onReportQuestion={reportCurrentQuestion}
      onRetryQuestion={retryCurrentQuestion}
      onToggleBookmark={toggleCurrentBookmark}
      onNextQuestion={goToNextQuestion}
      onPauseSession={pauseSession}
      onCompleteSession={completeSession}
      onPreviousQuestion={goToPreviousQuestion}
      onQuestionCountChange={setQuestionCount}
      onPreparationLevelChange={setPreparationLevel}
      onInterviewTypeChange={setInterviewType}
      onQuestionSelect={goToQuestion}
      onQuestionFocusClear={clearQuestionFocus}
      onRefreshRoles={refreshRoles}
      onRunCode={runCurrentCode}
      onSelectedFocusSkillsChange={updateSelectedFocusSkills}
      onSelectedFocusSkillToggle={toggleSelectedFocusSkill}
      onSelectedRoleChange={handleSelectedRoleChange}
      onResumeSession={resumeSession}
      onUpdateAnswer={updateCurrentAnswer}
      onUpdateCode={updateCurrentCode}
      onUpdateNote={updateCurrentNote}
      onUploadCv={uploadCv}
      plan={planResponse?.interview_plan ?? null}
      questionFocus={questionFocus}
      questionCount={questionCount}
      preparationLevel={preparationLevel}
      interviewType={interviewType}
      roles={roles}
      selectedRole={selectedRole}
      selectedFocusSkills={selectedFocusSkills}
      skillOptionsStatus={skillOptionsStatus}
      skillGroups={interviewContext?.skill_groups ?? planResponse?.context.skill_groups ?? {}}
    />
  );
}

function buildSessionPayload(
  planResponse: BuildInterviewPlanResponse,
  answersByQuestion: Record<string, string>,
  codeByQuestion: Record<string, string>,
  evaluations: Record<string, AnswerEvaluation>,
  learningPath: LearningPathItem[],
  currentQuestionIndex: number,
  notesByQuestion: Record<string, string>,
  bookmarkedQuestionIds: string[],
  retryCounts: Record<string, number>,
  elapsedSeconds: number,
): InterviewPracticeSessionPayload {
  return {
    plan_response: planResponse,
    answers_by_question: answersByQuestion,
    code_by_question: codeByQuestion,
    evaluations,
    learning_path: learningPath,
    current_question_index: currentQuestionIndex,
    notes_by_question: notesByQuestion,
    bookmarked_question_ids: bookmarkedQuestionIds,
    retry_counts: retryCounts,
    elapsed_seconds: elapsedSeconds,
  };
}
