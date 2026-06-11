import type {
  AnswerEvaluation,
  AppSettings,
  AuthUser,
  CodeRunResponse,
  ExtractJobSkillsResponse,
  InterviewContext,
  InterviewEngine,
  InterviewQuestion,
  InterviewPracticeSession,
  InterviewPracticeSessionPayload,
  InterviewProgressDashboard,
  LearningPathItem,
  MatchResponse,
  PreparationInterviewResponse,
  QuestionFocus,
  PreparationInterviewType,
  PreparationLevel,
  SkillWeights,
  UserSession,
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

export function getUserSessions(): Promise<UserSession[]> {
  return requestJson<UserSession[]>('/api/sessions');
}

export function getInterviewSessions(): Promise<InterviewPracticeSession[]> {
  return requestJson<InterviewPracticeSession[]>('/api/interview/sessions');
}

export function getInterviewProgress(): Promise<InterviewProgressDashboard> {
  return requestJson<InterviewProgressDashboard>('/api/interview/progress');
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
    }),
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
