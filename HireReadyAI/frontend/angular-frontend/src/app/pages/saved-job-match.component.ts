import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';

import { ApiService } from '../api.service';
import { MatchResultComponent } from '../components/match-result.component';
import { MatchResponse } from '../models';
import { errorDetail, fileFromEvent, textAreaValue } from '../ui.utils';

@Component({
  selector: 'app-saved-job-match',
  standalone: true,
  imports: [CommonModule, FormsModule, MatchResultComponent],
  styleUrl: '../app.scss',
  templateUrl: './saved-job-match.component.html',
})
export class SavedJobMatchComponent implements OnInit {
  roles: string[] = [];
  selectedRole = '';
  cvText = '';
  loading = false;
  loadingLabel = '';
  errorMessage = '';
  matchResult: MatchResponse | null = null;

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.refreshRoles();
  }

  refreshRoles(): void {
    this.api.getRoles().subscribe({
      next: ({ roles }) => {
        this.roles = roles;
        this.selectedRole = this.selectedRole || roles[0] || '';
      },
      error: (error) => this.setError(error),
    });
  }

  updateCvText(event: Event): void {
    this.cvText = textAreaValue(event);
  }

  uploadCv(event: Event): void {
    const file = fileFromEvent(event);
    if (!file) {
      return;
    }

    this.withLoading('Reading CV file');
    this.api
      .uploadCvText(file)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: ({ text }) => {
          this.cvText = text;
        },
        error: (error) => this.setError(error),
      });
  }

  calculateMatch(includeAllSavedJobs: boolean): void {
    if (!this.cvText.trim() || !this.selectedRole) {
      this.errorMessage = 'Add a CV and choose a target role.';
      return;
    }

    this.withLoading(includeAllSavedJobs ? 'Calculating other fit' : 'Calculating match');
    this.api
      .matchSavedJob(this.cvText, this.selectedRole, includeAllSavedJobs)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (result) => {
          this.matchResult = result;
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
