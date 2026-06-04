import { NavLink } from 'react-router-dom';

import { AppRoutes } from './AppRoutes';

export function App() {
  return (
    <main className="workspace">
      <nav className="site-navbar" aria-label="Main navigation">
        <div className="brand-stack">
          <NavLink className="brand-link" to="/">
            HireReadyAI
          </NavLink>
        </div>
        <div className="site-menu">
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
              <span className="nav-disabled">Adaptive interview</span>
            </div>
          </div>
        </div>
      </nav>

      <AppRoutes />
    </main>
  );
}
