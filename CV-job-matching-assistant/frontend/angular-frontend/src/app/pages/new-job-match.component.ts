import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';

import { ApiService } from '../api.service';
import { MatchResultComponent } from '../components/match-result.component';
import { MatchResponse } from '../models';
import { errorDetail, fileFromEvent, textAreaValue } from '../ui.utils';

@Component({
  selector: 'app-new-job-match',
  standalone: true,
  imports: [CommonModule, FormsModule, MatchResultComponent],
  styleUrl: '../app.scss',
  templateUrl: './new-job-match.component.html',
})
export class NewJobMatchComponent {
  cvText = '';
  jobDescriptionText = '';
  saveNewJobProfile = true;
  loading = false;
  loadingLabel = '';
  errorMessage = '';
  matchResult: MatchResponse | null = null;

  constructor(private readonly api: ApiService) {}

  updateCvText(event: Event): void {
    this.cvText = textAreaValue(event);
  }

  updateJobDescriptionText(event: Event): void {
    this.jobDescriptionText = textAreaValue(event);
  }

  uploadCv(event: Event): void {
    this.uploadText(event, 'cv');
  }

  uploadJobDescription(event: Event): void {
    this.uploadText(event, 'job');
  }

  calculateMatch(includeAllSavedJobs: boolean): void {
    if (!this.cvText.trim() || !this.jobDescriptionText.trim()) {
      this.errorMessage = 'Add a CV and a job description.';
      return;
    }

    this.withLoading(includeAllSavedJobs ? 'Calculating other fit' : 'Extracting job profile and matching');
    this.api
      .matchNewJob(this.cvText, this.jobDescriptionText, this.saveNewJobProfile, includeAllSavedJobs)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (result) => {
          this.matchResult = result;
        },
        error: (error) => this.setError(error),
      });
  }

  private uploadText(event: Event, type: 'cv' | 'job'): void {
    const file = fileFromEvent(event);
    if (!file) {
      return;
    }

    const isCv = type === 'cv';
    this.withLoading(isCv ? 'Reading CV file' : 'Reading job description');
    const uploadRequest = isCv ? this.api.uploadCvText(file) : this.api.uploadJobDescriptionText(file);

    uploadRequest.pipe(finalize(() => (this.loading = false))).subscribe({
      next: ({ text }) => {
        if (isCv) {
          this.cvText = text;
        } else {
          this.jobDescriptionText = text;
        }
      },
      error: (error) => this.setError(error),
    });
  }

  private withLoading(label: string): void {
    this.errorMessage = '';
    this.loading = true;
    this.loadingLabel = label;
  }

  private setError(error: unknown): void {
    this.errorMessage = errorDetail(error);
  }
}
