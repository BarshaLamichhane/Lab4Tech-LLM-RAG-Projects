import { ChangeEvent, useEffect, useRef, useState } from 'react';

import {
  buildInterviewContext,
  getRoles,
  startAdaptiveInterview,
  submitAdaptiveAnswer,
  uploadText,
} from '../api';
import type {
  AdaptiveInterviewResponse,
  GroundingIndexMode,
  InterviewContext,
  PreparationLevel,
  QuestionFocus,
  QuestionGenerationStrategy,
} from '../types';
import { errorMessage } from '../ui';
import { AdaptiveInterviewView } from './AdaptiveInterviewView';

export function AdaptiveInterviewPage() {
  const cvTextRef = useRef<HTMLTextAreaElement>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [role, setRole] = useState('');
  const [context, setContext] = useState<InterviewContext | null>(null);
  const [selectedFocus, setSelectedFocus] = useState<QuestionFocus | null>(null);
  const [selectedSkill, setSelectedSkill] = useState('');
  const [level, setLevel] = useState<PreparationLevel>('intermediate');
  const [maxTurns, setMaxTurns] = useState(5);
  const [generationStrategy, setGenerationStrategy] = useState<QuestionGenerationStrategy>('llm');
  const [groundingIndexMode, setGroundingIndexMode] = useState<GroundingIndexMode>('use_existing');
  const [groundingQuery, setGroundingQuery] = useState('');
  const [useCompanyContext, setUseCompanyContext] = useState(false);
  const [session, setSession] = useState<AdaptiveInterviewResponse | null>(null);
  const [answer, setAnswer] = useState('');
  const [code, setCode] = useState('');
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getRoles()
      .then((loaded) => {
        setRoles(loaded);
        setRole(loaded[0] ?? '');
      })
      .catch((caught) => setError(errorMessage(caught)));
  }, []);

  async function uploadCv(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    await runTask('Reading CV', async () => {
      const text = await uploadText(file, 'cv');
      if (cvTextRef.current) cvTextRef.current.value = text;
      await loadContext(text, role);
    });
  }

  async function loadContext(cvText = cvTextRef.current?.value.trim() ?? '', targetRole = role) {
    if (!cvText || !targetRole) return;
    await runTask('Comparing CV and role', async () => {
      setContext(await buildInterviewContext(cvText, { targetRole }));
      setSelectedFocus(null);
      setSelectedSkill('');
      setSession(null);
    });
  }

  async function changeRole(nextRole: string) {
    setRole(nextRole);
    setContext(null);
    setSelectedSkill('');
    setSelectedFocus(null);
    setSession(null);
    await loadContext(cvTextRef.current?.value.trim() ?? '', nextRole);
  }

  function selectSkill(focus: QuestionFocus, skill: string) {
    setSelectedFocus(skill ? focus : null);
    setSelectedSkill(skill);
  }

  async function start() {
    if (!context || !selectedSkill) return;
    await runTask('Starting adaptive interview', async () => {
      setSession(await startAdaptiveInterview({
        role,
        selectedSkill,
        level,
        maxTurns,
        context,
        generationStrategy,
        groundingQuery,
        groundingIndexMode,
        useCompanyContext,
        companyContext: companyContextFromProfile(context.job_profile),
      }));
      setAnswer('');
      setCode('');
    });
  }

  async function submit() {
    if (!session) return;
    const currentQuestion = session.next_question;
    const response = currentQuestion?.is_coding
      ? ['```python', code, '```', answer].join('\n')
      : answer;
    if (!response.trim()) return;
    await runTask('Scoring and adapting', async () => {
      setSession(await submitAdaptiveAnswer(session.state, response));
      setAnswer('');
      setCode('');
    });
  }

  function restart() {
    setSession(null);
    setAnswer('');
    setCode('');
  }

  async function runTask(label: string, task: () => Promise<void>) {
    setError('');
    setLoadingLabel(label);
    try {
      await task();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLoadingLabel('');
    }
  }

  return (
    <AdaptiveInterviewView
      answer={answer}
      code={code}
      context={context}
      cvTextRef={cvTextRef}
      error={error}
      generationStrategy={generationStrategy}
      groundingIndexMode={groundingIndexMode}
      groundingQuery={groundingQuery}
      level={level}
      loadingLabel={loadingLabel}
      maxTurns={maxTurns}
      onAnswerChange={setAnswer}
      onCodeChange={setCode}
      onCvBlur={() => loadContext()}
      onGenerationStrategyChange={setGenerationStrategy}
      onGroundingIndexModeChange={setGroundingIndexMode}
      onGroundingQueryChange={setGroundingQuery}
      onLevelChange={setLevel}
      onMaxTurnsChange={setMaxTurns}
      onRoleChange={changeRole}
      onRestart={restart}
      onSelectSkill={selectSkill}
      onStart={start}
      onSubmit={submit}
      onUploadCv={uploadCv}
      onUseCompanyContextChange={setUseCompanyContext}
      role={role}
      roles={roles}
      selectedFocus={selectedFocus}
      selectedSkill={selectedSkill}
      session={session}
      useCompanyContext={useCompanyContext}
      companyContext={companyContextFromProfile(context?.job_profile)}
    />
  );
}

function companyContextFromProfile(profile?: Record<string, unknown>): Record<string, string> {
  if (!profile) return {};
  return Object.fromEntries(
    ['company_name', 'company_context', 'industry_domain', 'business_problem'].flatMap((key) => {
      const value = profile[key];
      return typeof value === 'string' && value.trim() ? [[key, value.trim()]] : [];
    }),
  );
}
