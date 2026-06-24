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

export interface RoleResponse {
  roles: string[];
}

export interface TextUploadResponse {
  text: string;
}
