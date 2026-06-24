import type { SkillCategoryBreakdown } from '../types';

interface MatchChartsProps {
  breakdown: SkillCategoryBreakdown[];
}

function percent(row: SkillCategoryBreakdown) {
  return row.total_count ? Math.round((row.matched_count / row.total_count) * 100) : 0;
}

export function MatchCharts({ breakdown }: MatchChartsProps) {
  const rows = breakdown.filter((row) => row.total_count > 0);
  const center = 110;
  const radius = 82;
  const point = (index: number, value: number) => {
    const angle = (Math.PI * 2 * index) / rows.length - Math.PI / 2;
    const distance = radius * value / 100;
    return `${center + Math.cos(angle) * distance},${center + Math.sin(angle) * distance}`;
  };
  const axisPoints = rows.map((_, index) => point(index, 100)).join(' ');
  const scorePoints = rows.map((row, index) => point(index, percent(row))).join(' ');

  if (rows.length < 3) {
    return null;
  }

  return (
    <section className="chart-grid">
      <div className="panel chart-panel">
        <h2>Skill match radar</h2>
        <svg className="radar-chart" viewBox="0 0 220 220" role="img" aria-label="Skill category match radar">
          <polygon className="radar-grid" points={axisPoints} />
          {rows.map((_, index) => <line key={index} x1={center} y1={center} x2={point(index, 100).split(',')[0]} y2={point(index, 100).split(',')[1]} />)}
          <polygon className="radar-score" points={scorePoints} />
        </svg>
        <div className="radar-legend">
          {rows.map((row) => <span key={row.category}>{row.label}: <strong>{percent(row)}%</strong></span>)}
        </div>
      </div>
      <div className="panel chart-panel">
        <h2>Category-wise score</h2>
        <div className="category-bars">
          {rows.map((row) => (
            <div className="category-bar-row" key={row.category}>
              <div><span>{row.label}</span><strong>{row.matched_count}/{row.total_count}</strong></div>
              <div className="category-bar"><span style={{ width: `${percent(row)}%` }} /></div>
              <small>{percent(row)}% matched</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
