import { Link } from 'react-router-dom';

export function HomePage() {
  return (
    <>
      <section className="home-hero">
        <p className="eyebrow">HireReadyAI</p>
        <h1>Know your strengths. Find your perfect match. Land your dream job.</h1>
        <p>
          Use one workspace to understand job requirements, compare CVs with roles,
          and practise interview questions with scored feedback.
        </p>
      </section>

      <section className="home-grid">
        <article className="home-card">
          <div className="home-card-top">
            <span>Skill Extraction</span>
            <strong>01</strong>
          </div>
          <h2>Job skill extraction</h2>
          <p>Extract structured job skills, strongly required skills, responsibilities, tools, and soft skills.</p>
          <div className="home-actions">
            <Link to="/job-skill-extractor">Job skill extraction</Link>
          </div>
        </article>

        <article className="home-card">
          <div className="home-card-top">
            <span>Skill Matching</span>
            <strong>02</strong>
          </div>
          <h2>Compare CVs with target roles</h2>
          <p>Match a CV against saved job roles or a new job description and review matched and missing skills.</p>
          <div className="home-actions">
            <Link to="/saved-job-match">CV vs saved job role</Link>
            <Link to="/new-job-match">CV vs new job description</Link>
          </div>
        </article>

        <article className="home-card">
          <div className="home-card-top">
            <span>Interview Assistant</span>
            <strong>03</strong>
          </div>
          <h2>Preparation mode</h2>
          <p>Generate interview questions from selected skills, practise Python coding, and score answers.</p>
          <div className="home-actions">
            <Link to="/interview-practice">Preparation mode</Link>
            <Link to="/adaptive-interview">Adaptive interview</Link>
            <Link to="/adaptive-progress">Adaptive progress</Link>
          </div>
        </article>
      </section>
    </>
  );
}
