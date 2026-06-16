export interface CandidateProject {
  name: string;
  description: string;
  role: string;
  skills: string[];
  responsibilities: string[];
  outcomes: string[];
  links: string[];
}

export interface CandidateProfile {
  email: string | null;
  estimated_experience_years: number;
  skills: string[];
  projects: CandidateProject[];
}

export interface SkillMatch {
  target_role: string;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  matched_strongly_required_skills: string[];
  missing_strongly_required_skills: string[];
  candidate_skills: string[];
  total_possible_weight: number;
  matched_weight: number;
  score_breakdown: SkillCategoryBreakdown[];
}

export interface SkillCategoryBreakdown {
  category: string;
  label: string;
  weight: number;
  matched_count: number;
  total_count: number;
  matched_weight: number;
  total_weight: number;
  contribution_percent: number;
  matched_skills: string[];
  missing_skills: string[];
}

export interface SkillWeights {
  strongly_required_skills: number;
  required_skills: number;
  tools_and_platforms: number;
  preferred_skills: number;
  soft_skills: number;
}

export interface AuthUser {
  username: string;
  role: 'admin' | 'user';
}

export interface AppSettings {
  skill_weights: SkillWeights;
  skill_aliases: Record<string, string>;
  broad_skill_aliases: Record<string, string[]>;
}

export interface UserLLMSettings {
  provider: 'mistral' | 'openai';
  model_name: string;
  has_api_key: boolean;
  api_key_preview: string;
  updated_at: string | null;
}

export interface UserSession {
  id: string;
  username: string;
  session_type: string;
  title: string;
  created_at: string;
  updated_at: string;
  status: 'in_progress' | 'paused' | 'completed';
  payload: Record<string, unknown>;
}

export interface MatchResponse {
  candidate_profile: CandidateProfile;
  target_job_match: SkillMatch;
  target_job_profile: Record<string, unknown> | null;
  all_saved_job_matches: SkillMatch[];
}

export interface ExtractJobSkillsResponse {
  job_profile: Record<string, unknown>;
  saved_path: string | null;
}

export type QuestionType = 'technical' | 'coding' | 'behavioral' | 'project' | 'gap' | 'role_fit';
export type Difficulty = 'easy' | 'medium' | 'hard';
export type InterviewEngine = 'mistral';
export type PreparationLevel = 'beginner' | 'intermediate' | 'advanced';
export type PreparationInterviewType = 'technical_theory' | 'coding' | 'project' | 'behavioral' | 'mixed';
export type QuestionGenerationStrategy = 'llm' | 'grounded';
export type GroundingIndexMode = 'use_existing' | 'recreate' | 'update';
export type AdaptiveStartFocus = 'weak' | 'strong';
export type QuestionFocus =
  | 'all'
  | 'matched_strongly_required'
  | 'matched_skills'
  | 'matched_required'
  | 'missing_strongly_required'
  | 'missing_skills'
  | 'missing_required'
  | 'matched_tools'
  | 'missing_tools'
  | 'soft_skills'
  | 'responsibilities';

export interface InterviewContext {
  candidate_profile: Record<string, unknown>;
  job_profile: Record<string, unknown>;
  match_result: Record<string, unknown>;
  focus_skills: string[];
  gap_skills: string[];
  skill_groups: Partial<Record<QuestionFocus, string[]>>;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  question_type: QuestionType;
  difficulty: Difficulty;
  skill: string | null;
  source_group: QuestionFocus | 'adaptive' | null;
  is_coding: boolean;
  criteria_source: 'llm' | 'template';
  expected_points: string[];
  expected_point_weights: number[];
  follow_up_questions: string[];
  scoring_rubric: string[];
  hint: string;
  generation_strategy?: QuestionGenerationStrategy;
  grounding_used?: string[];
}

export interface GroundingSource {
  filename: string;
  size: number;
  hash: string;
  indexed: boolean;
  chunk_count: number;
  indexed_at: string | null;
}

export interface LearningPathItem {
  topic: string;
  priority: string;
  why_it_matters: string;
  subtopics: string[];
  practice_tasks: string[];
  sample_questions: string[];
  estimated_time: string;
}

export interface InterviewPlan {
  role: string;
  readiness_score: number;
  engine: InterviewEngine;
  question_focus: QuestionFocus[];
  selected_focus_skills: Partial<Record<QuestionFocus, string[]>>;
  interview_rounds: string[];
  questions: InterviewQuestion[];
  learning_path: LearningPathItem[];
  preparation_level?: PreparationLevel;
  interview_type?: PreparationInterviewType;
  use_company_context?: boolean;
  company_context?: Record<string, string>;
}

export interface BuildInterviewPlanResponse {
  context: InterviewContext;
  interview_plan: InterviewPlan;
}

export interface InterviewPracticeSessionPayload {
  plan_response: BuildInterviewPlanResponse;
  answers_by_question: Record<string, string>;
  code_by_question: Record<string, string>;
  evaluations: Record<string, AnswerEvaluation>;
  learning_path: LearningPathItem[];
  current_question_index: number;
  notes_by_question: Record<string, string>;
  bookmarked_question_ids: string[];
  retry_counts: Record<string, number>;
  elapsed_seconds: number;
}

export interface InterviewPracticeSession extends Omit<UserSession, 'payload'> {
  payload: InterviewPracticeSessionPayload;
}

export interface PreparationInterviewResponse {
  role: string;
  selected_skills: string[];
  level: PreparationLevel;
  interview_type: PreparationInterviewType;
  questions: InterviewQuestion[];
}

export interface CodeRunResponse {
  stdout: string;
  stderr: string;
  exit_code: number | null;
  timed_out: boolean;
}

export interface AnswerEvaluation {
  score: number;
  rating: string;
  strengths: string[];
  weaknesses: string[];
  missing_points: string[];
  feedback: string;
  improved_answer_outline: string[];
  follow_up_question: string | null;
  learning_recommendations: string[];
  expected_point_assessments: ExpectedPointAssessment[];
  score_breakdown: ScoreBreakdownItem[];
}

export interface AdaptiveInterviewTurn {
  question: InterviewQuestion;
  answer: string | null;
  evaluation: AnswerEvaluation | null;
  selected_skill: string | null;
  decision_reason: string;
}

export interface AdaptiveSkillProfile {
  skill: string;
  source_group: string;
  priority: number;
  cv_status: 'matched' | 'missing' | 'unknown';
  job_importance: string;
  estimated_score: number;
  attempts: number;
  average_score: number | null;
  last_score: number | null;
  status: 'weak' | 'developing' | 'strong';
}

export interface AdaptiveLearnerProfile {
  goal_role: string;
  readiness_score: number;
  skills: AdaptiveSkillProfile[];
  strongest_skills: string[];
  weakest_skills: string[];
  next_focus: string | null;
}

export interface AdaptiveInterviewState {
  role: string;
  selected_skills: string[];
  level: PreparationLevel;
  max_turns: number;
  start_focus: AdaptiveStartFocus;
  context: InterviewContext | null;
  generation_strategy: QuestionGenerationStrategy;
  grounding_query: string | null;
  grounding_index_mode: GroundingIndexMode;
  use_company_context: boolean;
  company_context: Record<string, string> | null;
  learner_profile: AdaptiveLearnerProfile | null;
  current_skill: string | null;
  current_decision_reason: string;
  turns: AdaptiveInterviewTurn[];
}

export interface AdaptiveInterviewResponse {
  state: AdaptiveInterviewState;
  next_question: InterviewQuestion | null;
  finished: boolean;
  final_summary: {
    summary?: unknown;
    strongest_points?: unknown[];
    improvement_areas?: unknown[];
    recommended_next_steps?: unknown[];
  } | null;
}

export interface ExpectedPointAssessment {
  point: string;
  weight: number;
  awarded_score: number;
  explanation: string;
}

export interface ScoreBreakdownItem {
  category: 'technical_correctness' | 'completeness' | 'communication' | 'examples' | 'code_quality';
  label: string;
  max_score: number;
  awarded_score: number;
  explanation: string;
}

export interface InterviewProgressDashboard {
  sessions: number;
  answered_questions: number;
  overall_average: number;
  average_by_skill: { skill: string; average_score: number; attempts: number }[];
  average_by_type: { type: string; average_score: number; attempts: number }[];
  score_trend: { date: string; role: string; average_score: number }[];
  strongest_topics: { skill: string; average_score: number; attempts: number }[];
  weakest_topics: { skill: string; average_score: number; attempts: number }[];
  retry_questions: { session_id: string; question_id: string; question: string; skill: string; score: number }[];
  recommended_next_session: { skills: string[]; reason: string };
}

export interface AdaptiveProgressDashboard {
  sessions: number;
  answered_questions: number;
  overall_average: number;
  latest_readiness_score: number;
  average_by_skill: { skill: string; average_score: number; attempts: number }[];
  strongest_skills: string[];
  weakest_skills: string[];
  skill_status_counts: { weak: number; developing: number; strong: number };
  readiness_trend: { date: string; role: string; readiness_score: number; average_score: number }[];
  recent_reports: {
    session_id: string;
    title: string;
    date: string;
    role: string;
    average_score: number;
    readiness_score: number;
    summary: string;
  }[];
  recommended_next_session: { skills: string[]; reason: string };
}
