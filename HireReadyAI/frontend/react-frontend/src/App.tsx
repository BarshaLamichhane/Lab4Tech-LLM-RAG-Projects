import { NavLink } from 'react-router-dom';

import { AppRoutes } from './AppRoutes';
import { useAuth } from './AuthContext';

export function App() {
  const { user, logout } = useAuth();

  return (
    <main className="workspace">
      <nav className="site-navbar" aria-label="Main navigation">
        <div className="brand-stack">
          <NavLink className="brand-link" to="/">
            HireReadyAI
          </NavLink>
        </div>
        {user && <div className="site-menu">
          <NavLink to="/" end>
            Home
          </NavLink>

          <div className="nav-menu-group">
            <button type="button">Skill Extraction</button>
            <div className="nav-dropdown">
              <NavLink to="/job-skill-extractor">Job skill extraction</NavLink>
            </div>
          </div>

          <div className="nav-menu-group">
            <button type="button">Skill Matching</button>
            <div className="nav-dropdown">
              <NavLink to="/saved-job-match">CV vs saved job role</NavLink>
              <NavLink to="/new-job-match">CV vs new job description</NavLink>
            </div>
          </div>

          <div className="nav-menu-group">
            <button type="button">Interview Assistant</button>
            <div className="nav-dropdown">
              <NavLink to="/interview-practice">Preparation mode</NavLink>
              <NavLink to="/adaptive-interview">Adaptive interview</NavLink>
              {user.role === 'admin' && <NavLink to="/learning-scoring">Learning & scoring</NavLink>}
              <NavLink to="/interview-progress">Preparation progress</NavLink>
              <NavLink to="/adaptive-progress">Adaptive progress</NavLink>
            </div>
          </div>
          <NavLink to="/account">Account</NavLink>
          {user.role === 'admin' && <NavLink to="/admin/users">Users</NavLink>}
          {user.role === 'admin' && <NavLink to="/admin/settings">Settings</NavLink>}
          {user.role === 'admin' && <NavLink to="/admin/evaluation/job-descriptions">Evaluation data</NavLink>}
          <span className="user-badge">{user.username} · {user.role}</span>
          <button className="nav-logout" type="button" onClick={logout}>Sign out</button>
        </div>}
      </nav>
      <AppRoutes />
    </main>
  );
}
