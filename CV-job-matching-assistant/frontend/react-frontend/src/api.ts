import type {
  AnswerEvaluation,
  AdaptiveProgressDashboard,
  AdaptiveInterviewResponse,
  AdaptiveInterviewState,
  AppSettings,
  AuthUser,
  CodeRunResponse,
  ExtractJobSkillsResponse,
  InterviewContext,
  InterviewEngine,
  InterviewQuestion,
  GroundingContextChunk,
  GroundingIndexMode,
  GroundingChunk,
  GroundingSource,
  InterviewPracticeSession,
  InterviewPracticeSessionPayload,
  InterviewProgressDashboard,
  LearningPathItem,
  MatchResponse,
  PreparationInterviewResponse,
  QuestionFocus,
  QuestionGenerationStrategy,
  PreparationInterviewType,
  PreparationLevel,
  SkillWeights,
  UserLLMSettings,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '');

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 && path !== '/api/auth/login') {
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function loginUser(username: string, password: string): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function getCurrentUser(): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/auth/me');
}

export async function logoutUser(): Promise<void> {
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return requestJson<void>('/api/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export function getUserLLMSettings(): Promise<UserLLMSettings> {
  return requestJson<UserLLMSettings>('/api/account/llm-settings');
}

export function updateUserLLMSettings(options: {
  provider: 'mistral' | 'openai';
  modelName: string;
  apiKey?: string;
  clearApiKey?: boolean;
}): Promise<UserLLMSettings> {
  return requestJson<UserLLMSettings>('/api/account/llm-settings', {
    method: 'PUT',
    body: JSON.stringify({
      provider: options.provider,
      model_name: options.modelName,
      api_key: options.apiKey || null,
      clear_api_key: Boolean(options.clearApiKey),
    }),
  });
}

export function getAdminSettings(): Promise<AppSettings> {
  return requestJson<AppSettings>('/api/admin/settings');
}

export function updateAdminSettings(settings: AppSettings): Promise<AppSettings> {
  return requestJson<AppSettings>('/api/admin/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export function createUser(
  username: string,
  password: string,
  role: AuthUser['role'],
): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/admin/users', {
    method: 'POST',
    body: JSON.stringify({ username, password, role }),
  });
}

export function getInterviewSessions(): Promise<InterviewPracticeSession[]> {
  return requestJson<InterviewPracticeSession[]>('/api/interview/sessions');
}

export function getInterviewProgress(): Promise<InterviewProgressDashboard> {
  return requestJson<InterviewProgressDashboard>('/api/interview/progress');
}

export function getAdaptiveProgress(): Promise<AdaptiveProgressDashboard> {
  return requestJson<AdaptiveProgressDashboard>('/api/interview/adaptive/progress');
}

export function createInterviewSession(
  title: string,
  payload: InterviewPracticeSessionPayload,
): Promise<InterviewPracticeSession> {
  return requestJson<InterviewPracticeSession>('/api/interview/sessions', {
    method: 'POST',
    body: JSON.stringify({ title, status: 'in_progress', payload }),
  });
}

export function updateInterviewSession(
  sessionId: string,
  title: string,
  status: InterviewPracticeSession['status'],
  payload: InterviewPracticeSessionPayload,
): Promise<InterviewPracticeSession> {
  return requestJson<InterviewPracticeSession>(`/api/interview/sessions/${sessionId}`, {
    method: 'PUT',
    body: JSON.stringify({ title, status, payload }),
  });
}

export async function getRoles(): Promise<string[]> {
  const response = await requestJson<{ roles: string[] }>('/api/job-roles');
  return response.roles;
}

export async function uploadText(file: File, kind: 'cv' | 'job'): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const path = kind === 'cv' ? '/api/uploads/cv-text' : '/api/uploads/job-description-text';

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Upload failed with ${response.status}`);
  }

  const payload = (await response.json()) as { text: string };
  return payload.text;
}

export function matchSavedJob(
  cvText: string,
  targetRole: string,
  includeAllSavedJobs: boolean,
  skillWeights?: SkillWeights,
): Promise<MatchResponse> {
  return requestJson<MatchResponse>('/api/match/saved-job', {
    method: 'POST',
    body: JSON.stringify({
      cv_text: cvText,
      target_role: targetRole,
      include_all_saved_jobs: includeAllSavedJobs,
      skill_weights: skillWeights,
    }),
  });
}

export function matchNewJob(
  cvText: string,
  jobDescriptionText: string,
  saveNewJobProfile: boolean,
  includeAllSavedJobs: boolean,
  skillWeights?: SkillWeights,
): Promise<MatchResponse> {
  return requestJson<MatchResponse>('/api/match/new-job', {
    method: 'POST',
    body: JSON.stringify({
      cv_text: cvText,
      job_description_text: jobDescriptionText,
      save_new_job_profile: saveNewJobProfile,
      include_all_saved_jobs: includeAllSavedJobs,
      skill_weights: skillWeights,
    }),
  });
}

export function extractJobSkills(
  jobDescriptionText: string,
  saveJobProfile: boolean,
): Promise<ExtractJobSkillsResponse> {
  return requestJson<ExtractJobSkillsResponse>('/api/job-skills/extract', {
    method: 'POST',
    body: JSON.stringify({
      job_description_text: jobDescriptionText,
      save_job_profile: saveJobProfile,
    }),
  });
}

export function buildInterviewContext(
  cvText: string,
  options: {
    jobDescriptionText?: string;
    targetRole?: string;
  },
): Promise<InterviewContext> {
  return requestJson<InterviewContext>('/api/interview/context', {
    method: 'POST',
    body: JSON.stringify({
      cv_text: cvText,
      job_description_text: options.jobDescriptionText || null,
      target_role: options.targetRole || null,
    }),
  });
}

export function generatePreparationInterview(
  role: string,
  selectedSkills: string[],
  candidateProjects: Record<string, unknown>[],
  questionCount: number,
  level: PreparationLevel,
  interviewType: PreparationInterviewType,
  generationStrategy: QuestionGenerationStrategy = 'llm',
  groundingQuery?: string,
  groundingIndexMode: GroundingIndexMode = 'use_existing',
  useCompanyContext = false,
  companyContext?: Record<string, string>,
): Promise<PreparationInterviewResponse> {
  return requestJson<PreparationInterviewResponse>('/api/interview/preparation', {
    method: 'POST',
    body: JSON.stringify({
      role,
      selected_skills: selectedSkills,
      candidate_projects: candidateProjects,
      question_count: questionCount,
      level,
      interview_type: interviewType,
      generation_strategy: generationStrategy,
      grounding_query: groundingQuery || null,
      grounding_index_mode: groundingIndexMode,
      use_company_context: useCompanyContext,
      company_context: companyContext || null,
    }),
  });
}

export function getGroundingSources(): Promise<GroundingSource[]> {
  return requestJson<GroundingSource[]>('/api/interview/grounding/sources');
}

export function getGroundingChunks(): Promise<GroundingChunk[]> {
  return requestJson<GroundingChunk[]>('/api/interview/grounding/chunks');
}

export async function uploadGroundingDocuments(files: FileList): Promise<GroundingSource[]> {
  const body = new FormData();
  Array.from(files).forEach((file) => body.append('files', file));
  const response = await fetch(`${API_BASE_URL}/api/interview/grounding/upload`, {
    method: 'POST',
    credentials: 'include',
    body,
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Upload failed with ${response.status}`);
  }
  return ((await response.json()) as { sources: GroundingSource[] }).sources;
}

export function uploadGroundingUrl(url: string): Promise<{ sources: GroundingSource[] }> {
  return requestJson('/api/interview/grounding/url', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export function uploadGroundingText(text: string, filename = 'pasted_grounding_material.txt'): Promise<{ sources: GroundingSource[] }> {
  return requestJson('/api/interview/grounding/text', {
    method: 'POST',
    body: JSON.stringify({ text, filename }),
  });
}

export function buildGroundingIndex(
  mode: GroundingIndexMode,
  chunkSize = 900,
  chunkOverlap = 150,
): Promise<{ sources: GroundingSource[]; indexed_chunks: number | null }> {
  return requestJson('/api/interview/grounding/index', {
    method: 'POST',
    body: JSON.stringify({
      mode,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }),
  });
}

export function retrieveGroundingPreview(query: string, topK = 5): Promise<GroundingContextChunk[]> {
  return requestJson<GroundingContextChunk[]>('/api/interview/grounding/retrieve', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function regeneratePreparationQuestion(
  role: string,
  selectedSkills: string[],
  candidateProjects: Record<string, unknown>[],
  level: PreparationLevel,
  interviewType: PreparationInterviewType,
  questionId: string,
  existingQuestions: InterviewQuestion[],
  useCompanyContext = false,
  companyContext?: Record<string, string>,
): Promise<InterviewQuestion> {
  return requestJson<InterviewQuestion>('/api/interview/preparation/regenerate', {
    method: 'POST',
    body: JSON.stringify({
      role,
      selected_skills: selectedSkills,
      candidate_projects: candidateProjects,
      level,
      interview_type: interviewType,
      question_id: questionId,
      existing_questions: existingQuestions,
      use_company_context: useCompanyContext,
      company_context: companyContext || null,
    }),
  });
}

export function reportInterviewQuestion(
  question: InterviewQuestion,
  reason: 'irrelevant' | 'incorrect' | 'duplicate' | 'poor_quality' | 'other',
  comment = '',
): Promise<{ id: string; status: string }> {
  return requestJson('/api/interview/questions/report', {
    method: 'POST',
    body: JSON.stringify({ question, reason, comment }),
  });
}

export function evaluateInterviewAnswer(
  question: InterviewQuestion,
  answer: string,
  context: InterviewContext,
  interviewEngine: InterviewEngine,
): Promise<AnswerEvaluation> {
  return requestJson<AnswerEvaluation>('/api/interview/evaluate-answer', {
    method: 'POST',
    body: JSON.stringify({
      question,
      answer,
      context,
      interview_engine: interviewEngine,
    }),
  });
}

export function buildLearningPath(
  context: InterviewContext,
  evaluations: AnswerEvaluation[],
): Promise<LearningPathItem[]> {
  return requestJson<LearningPathItem[]>('/api/interview/learning-path', {
    method: 'POST',
    body: JSON.stringify({
      context,
      evaluations,
    }),
  });
}

export function runPythonCode(
  code: string,
  stdin = '',
  timeoutSeconds = 3,
): Promise<CodeRunResponse> {
  return requestJson<CodeRunResponse>('/api/interview/code/run', {
    method: 'POST',
    body: JSON.stringify({
      code,
      stdin,
      timeout_seconds: timeoutSeconds,
    }),
  });
}

export function startAdaptiveInterview(options: {
  role: string;
  level: PreparationLevel;
  maxTurns: number;
  startFocus: 'weak' | 'strong';
  context: InterviewContext;
  generationStrategy: QuestionGenerationStrategy;
  groundingQuery?: string;
  groundingIndexMode: GroundingIndexMode;
  useCompanyContext: boolean;
  companyContext?: Record<string, string>;
}): Promise<AdaptiveInterviewResponse> {
  return requestJson<AdaptiveInterviewResponse>('/api/interview/adaptive/start', {
    method: 'POST',
    body: JSON.stringify({
      role: options.role,
      selected_skills: [],
      level: options.level,
      max_turns: options.maxTurns,
      start_focus: options.startFocus,
      context: options.context,
      generation_strategy: options.generationStrategy,
      grounding_query: options.groundingQuery || null,
      grounding_index_mode: options.groundingIndexMode,
      use_company_context: options.useCompanyContext,
      company_context: options.companyContext || null,
    }),
  });
}

export function submitAdaptiveAnswer(
  state: AdaptiveInterviewState,
  answer: string,
): Promise<AdaptiveInterviewResponse> {
  return requestJson<AdaptiveInterviewResponse>('/api/interview/adaptive/answer', {
    method: 'POST',
    body: JSON.stringify({ state, answer }),
  });
}
