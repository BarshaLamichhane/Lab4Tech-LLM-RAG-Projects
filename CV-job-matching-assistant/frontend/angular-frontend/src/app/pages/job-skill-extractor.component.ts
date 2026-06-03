import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';

import { ApiService } from '../api.service';
import { ExtractJobSkillsResponse } from '../models';
import { downloadJson, errorDetail, fileFromEvent, textAreaValue } from '../ui.utils';

@Component({
  selector: 'app-job-skill-extractor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../app.scss',
  templateUrl: './job-skill-extractor.component.html',
})
export class JobSkillExtractorComponent {
  jobDescriptionText = '';
  saveJobProfile = true;
  loading = false;
  loadingLabel = '';
  errorMessage = '';
  extractionResult: ExtractJobSkillsResponse | null = null;

  constructor(private readonly api: ApiService) {}

  updateJobDescriptionText(event: Event): void {
    this.jobDescriptionText = textAreaValue(event);
  }

  uploadJobDescription(event: Event): void {
    const file = fileFromEvent(event);
    if (!file) {
      return;
    }

    this.withLoading('Reading job description');
    this.api
      .uploadJobDescriptionText(file)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: ({ text }) => {
          this.jobDescriptionText = text;
        },
        error: (error) => this.setError(error),
      });
  }

  extractSkills(): void {
    if (!this.jobDescriptionText.trim()) {
      this.errorMessage = 'Add a job description.';
      return;
    }

    this.withLoading('Extracting job skills');
    this.api
      .extractJobSkills(this.jobDescriptionText, this.saveJobProfile)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (result) => {
          this.extractionResult = result;
        },
        error: (error) => this.setError(error),
      });
  }

  download(): void {
    if (this.extractionResult) {
      downloadJson(this.extractionResult.job_profile, 'job-profile.json');
    }
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
