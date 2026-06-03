import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';

import {
  buildInterviewContext,
  buildLearningPath,
  evaluateInterviewAnswer,
  generatePreparationInterview,
  getRoles,
  runPythonCode,
  uploadText,
} from '../api';
import type {
  AnswerEvaluation,
  BuildInterviewPlanResponse,
  CodeRunResponse,
  InterviewContext,
  InterviewQuestion,
  LearningPathItem,
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
  const [interviewContext, setInterviewContext] = useState<InterviewContext | null>(null);
  const [planResponse, setPlanResponse] = useState<BuildInterviewPlanResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [evaluations, setEvaluations] = useState<Record<string, AnswerEvaluation>>({});
  const [codeByQuestion, setCodeByQuestion] = useState<Record<string, string>>({});
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
  }, []);

  async function refreshRoles() {
    try {
      const loadedRoles = await getRoles();
      setRoles(loadedRoles);
      setSelectedRole((currentRole) => currentRole || loadedRoles[0] || '');
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
    setLearningPath([]);
    setEvaluations({});
    setCodeByQuestion({});
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
      const preparationResponse = await generatePreparationInterview(role, selectedSkills, questionCount);
      const context = interviewContext ?? {
        candidate_profile: {},
        job_profile: { role },
        match_result: { score: 0 },
        focus_skills: selectedSkills,
        gap_skills: [],
        skill_groups: {},
      };
      setPlanResponse({
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
        },
      });
      setLearningPath([]);
      setEvaluations({});
      setCodeByQuestion({});
      setCodeRunResult(null);
      setCurrentQuestionIndex(0);
      if (answerRef.current) {
        answerRef.current.value = '';
      }
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

    const writtenAnswer = answerRef.current?.value.trim() ?? '';
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
    if (answerRef.current) {
      answerRef.current.value = '';
    }
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
      averageScore={averageScore}
      currentEvaluation={currentEvaluation}
      currentQuestion={currentQuestion}
      currentQuestionIndex={currentQuestionIndex}
      codeRunResult={codeRunResult}
      codeValue={currentQuestion ? codeByQuestion[currentQuestion.id] ?? '' : ''}
      cvTextRef={cvTextRef}
      error={error}
      evaluations={evaluations}
      learningPath={learningPath}
      loading={loading}
      loadingLabel={loadingLabel}
      onCvBlur={handleCvBlur}
      onEvaluateAnswer={evaluateCurrentAnswer}
      onGeneratePlan={generatePlan}
      onNextQuestion={goToNextQuestion}
      onPreviousQuestion={goToPreviousQuestion}
      onQuestionCountChange={setQuestionCount}
      onQuestionSelect={goToQuestion}
      onQuestionFocusClear={clearQuestionFocus}
      onRefreshRoles={refreshRoles}
      onRunCode={runCurrentCode}
      onSelectedFocusSkillsChange={updateSelectedFocusSkills}
      onSelectedFocusSkillToggle={toggleSelectedFocusSkill}
      onSelectedRoleChange={handleSelectedRoleChange}
      onUpdateCode={updateCurrentCode}
      onUploadCv={uploadCv}
      plan={planResponse?.interview_plan ?? null}
      questionFocus={questionFocus}
      questionCount={questionCount}
      roles={roles}
      selectedRole={selectedRole}
      selectedFocusSkills={selectedFocusSkills}
      skillOptionsStatus={skillOptionsStatus}
      skillGroups={interviewContext?.skill_groups ?? planResponse?.context.skill_groups ?? {}}
    />
  );
}
