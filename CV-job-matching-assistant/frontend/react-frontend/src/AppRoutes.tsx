import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './AuthContext';
import { AdminSettingsPage } from './pages/AdminSettingsPage';
import { HomePage } from './pages/HomePage';
import { JobSkillExtractorPage } from './pages/JobSkillExtractorPage';
import { InterviewPracticePage } from './pages/InterviewPracticePage';
import { LoginPage } from './pages/LoginPage';
import { NewJobMatchPage } from './pages/NewJobMatchPage';
import { SavedJobMatchPage } from './pages/SavedJobMatchPage';
import { SessionHistoryPage } from './pages/SessionHistoryPage';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user?.role === 'admin' ? children : <Navigate to="/" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/saved-job-match" element={<ProtectedRoute><SavedJobMatchPage /></ProtectedRoute>} />
      <Route path="/new-job-match" element={<ProtectedRoute><NewJobMatchPage /></ProtectedRoute>} />
      <Route path="/job-skill-extractor" element={<ProtectedRoute><JobSkillExtractorPage /></ProtectedRoute>} />
      <Route path="/interview-practice" element={<ProtectedRoute><InterviewPracticePage /></ProtectedRoute>} />
      <Route path="/sessions" element={<ProtectedRoute><SessionHistoryPage /></ProtectedRoute>} />
      <Route path="/admin/settings" element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
