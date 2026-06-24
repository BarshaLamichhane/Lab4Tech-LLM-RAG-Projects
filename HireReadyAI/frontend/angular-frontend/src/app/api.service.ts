import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ExtractJobSkillsResponse,
  MatchResponse,
  RoleResponse,
  TextUploadResponse,
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly apiBaseUrl = 'http://localhost:8000';

  constructor(private readonly http: HttpClient) {}

  getRoles(): Observable<RoleResponse> {
    return this.http.get<RoleResponse>(`${this.apiBaseUrl}/api/job-roles`);
  }

  uploadCvText(file: File): Observable<TextUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<TextUploadResponse>(`${this.apiBaseUrl}/api/uploads/cv-text`, formData);
  }

  uploadJobDescriptionText(file: File): Observable<TextUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<TextUploadResponse>(`${this.apiBaseUrl}/api/uploads/job-description-text`, formData);
  }

  matchSavedJob(cvText: string, targetRole: string, includeAllSavedJobs: boolean): Observable<MatchResponse> {
    return this.http.post<MatchResponse>(`${this.apiBaseUrl}/api/match/saved-job`, {
      cv_text: cvText,
      target_role: targetRole,
      include_all_saved_jobs: includeAllSavedJobs,
    });
  }

  matchNewJob(
    cvText: string,
    jobDescriptionText: string,
    saveNewJobProfile: boolean,
    includeAllSavedJobs: boolean,
  ): Observable<MatchResponse> {
    return this.http.post<MatchResponse>(`${this.apiBaseUrl}/api/match/new-job`, {
      cv_text: cvText,
      job_description_text: jobDescriptionText,
      save_new_job_profile: saveNewJobProfile,
      include_all_saved_jobs: includeAllSavedJobs,
    });
  }

  extractJobSkills(jobDescriptionText: string, saveJobProfile: boolean): Observable<ExtractJobSkillsResponse> {
    return this.http.post<ExtractJobSkillsResponse>(`${this.apiBaseUrl}/api/job-skills/extract`, {
      job_description_text: jobDescriptionText,
      save_job_profile: saveJobProfile,
    });
  }
}
