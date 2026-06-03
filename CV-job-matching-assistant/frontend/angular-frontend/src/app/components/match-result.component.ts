import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

import { MatchResponse } from '../models';
import { downloadJson } from '../ui.utils';

@Component({
  selector: 'app-match-result',
  standalone: true,
  imports: [CommonModule],
  styleUrl: '../app.scss',
  templateUrl: './match-result.component.html',
})
export class MatchResultComponent {
  @Input({ required: true }) result!: MatchResponse;

  download(): void {
    downloadJson(this.result, 'cv-match-result.json');
  }
}
