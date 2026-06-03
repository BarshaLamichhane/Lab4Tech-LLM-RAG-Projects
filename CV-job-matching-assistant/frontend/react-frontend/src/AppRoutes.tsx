import { Navigate, Route, Routes } from 'react-router-dom';

import { HomePage } from './pages/HomePage';
import { JobSkillExtractorPage } from './pages/JobSkillExtractorPage';
import { InterviewPracticePage } from './pages/InterviewPracticePage';
import { NewJobMatchPage } from './pages/NewJobMatchPage';
import { SavedJobMatchPage } from './pages/SavedJobMatchPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/saved-job-match" element={<SavedJobMatchPage />} />
      <Route path="/new-job-match" element={<NewJobMatchPage />} />
      <Route path="/job-skill-extractor" element={<JobSkillExtractorPage />} />
      <Route path="/interview-practice" element={<InterviewPracticePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
