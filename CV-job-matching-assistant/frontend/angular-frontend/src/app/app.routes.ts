import { Routes } from '@angular/router';

import { JobSkillExtractorComponent } from './pages/job-skill-extractor.component';
import { NewJobMatchComponent } from './pages/new-job-match.component';
import { SavedJobMatchComponent } from './pages/saved-job-match.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'saved-job-match' },
  { path: 'saved-job-match', component: SavedJobMatchComponent },
  { path: 'new-job-match', component: NewJobMatchComponent },
  { path: 'job-skill-extractor', component: JobSkillExtractorComponent },
  { path: '**', redirectTo: 'saved-job-match' },
];
