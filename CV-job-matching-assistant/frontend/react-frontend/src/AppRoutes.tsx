import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './AuthContext';
import { AccountPage } from './pages/AccountPage';
import { AdminSettingsPage } from './pages/AdminSettingsPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { HomePage } from './pages/HomePage';
import { JobSkillExtractorPage } from './pages/JobSkillExtractorPage';
import { InterviewPracticePage } from './pages/InterviewPracticePage';
import { InterviewProgressPage } from './pages/InterviewProgressPage';
import { LoginPage } from './pages/LoginPage';
import { NewJobMatchPage } from './pages/NewJobMatchPage';
import { SavedJobMatchPage } from './pages/SavedJobMatchPage';
import { SessionHistoryPage } from './pages/SessionHistoryPage';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <section className="status-row"><div className="status loading">Checking session...</div></section>;
  return user ? children : <Navigate to="/login" replace />;
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <section className="status-row"><div className="status loading">Checking session...</div></section>;
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
      <Route path="/interview-progress" element={<ProtectedRoute><InterviewProgressPage /></ProtectedRoute>} />
      <Route path="/sessions" element={<ProtectedRoute><SessionHistoryPage /></ProtectedRoute>} />
      <Route path="/account" element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
      <Route path="/admin/settings" element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
      <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
