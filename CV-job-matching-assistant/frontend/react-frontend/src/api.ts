import type {
  AnswerEvaluation,
  CodeRunResponse,
  ExtractJobSkillsResponse,
  InterviewContext,
  InterviewEngine,
  InterviewQuestion,
  LearningPathItem,
  MatchResponse,
  PreparationInterviewResponse,
  QuestionFocus,
} from './types';

const API_BASE_URL = 'http://localhost:8000';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
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
): Promise<MatchResponse> {
  return requestJson<MatchResponse>('/api/match/saved-job', {
    method: 'POST',
    body: JSON.stringify({
      cv_text: cvText,
      target_role: targetRole,
      include_all_saved_jobs: includeAllSavedJobs,
    }),
  });
}

export function matchNewJob(
  cvText: string,
  jobDescriptionText: string,
  saveNewJobProfile: boolean,
  includeAllSavedJobs: boolean,
): Promise<MatchResponse> {
  return requestJson<MatchResponse>('/api/match/new-job', {
    method: 'POST',
    body: JSON.stringify({
      cv_text: cvText,
      job_description_text: jobDescriptionText,
      save_new_job_profile: saveNewJobProfile,
      include_all_saved_jobs: includeAllSavedJobs,
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
