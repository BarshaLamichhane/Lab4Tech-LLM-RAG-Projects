import type {
  AnswerEvaluation,
  AppSettings,
  AuthUser,
  CodeRunResponse,
  ExtractJobSkillsResponse,
  InterviewContext,
  InterviewEngine,
  InterviewQuestion,
  LearningPathItem,
  MatchResponse,
  PreparationInterviewResponse,
  QuestionFocus,
  SkillWeights,
  UserSession,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');
  Object.entries(authHeader()).forEach(([key, value]) => headers.set(key, value));

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function authHeader(): Record<string, string> {
  const saved = localStorage.getItem('hire-ready-user');
  if (!saved) {
    return {};
  }
  const user = JSON.parse(saved) as AuthUser;
  return { Authorization: `Bearer ${user.token}` };
}

export function loginUser(username: string, password: string): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
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

export function getUserSessions(): Promise<UserSession[]> {
  return requestJson<UserSession[]>('/api/sessions');
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
    headers: authHeader(),
    body: formData,
  });

  if (!response.ok) {
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
  questionCount: number,
  level = 'intermediate',
): Promise<PreparationInterviewResponse> {
  return requestJson<PreparationInterviewResponse>('/api/interview/preparation', {
    method: 'POST',
    body: JSON.stringify({
      role,
      selected_skills: selectedSkills,
      question_count: questionCount,
      level,
    }),
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
