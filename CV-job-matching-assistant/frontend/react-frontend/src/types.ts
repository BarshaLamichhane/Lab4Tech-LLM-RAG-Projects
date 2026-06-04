export interface CandidateProfile {
  email: string | null;
  estimated_experience_years: number;
  skills: string[];
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
}

export interface SkillWeights {
  strongly_required_skills: number;
  required_skills: number;
  tools_and_platforms: number;
  preferred_skills: number;
  soft_skills: number;
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

export type QuestionType = 'technical' | 'behavioral' | 'project' | 'gap' | 'role_fit';
export type Difficulty = 'easy' | 'medium' | 'hard';
export type InterviewEngine = 'mistral';
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
  source_group: QuestionFocus | null;
  expected_points: string[];
  follow_up_questions: string[];
  scoring_rubric: string[];
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
}

export interface BuildInterviewPlanResponse {
  context: InterviewContext;
  interview_plan: InterviewPlan;
}

export interface PreparationInterviewResponse {
  role: string;
  selected_skills: string[];
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
}
