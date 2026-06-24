import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { SkillWeights } from '../types';

interface SkillWeightSettingsProps {
  defaultWeights: SkillWeights;
  weights: SkillWeights;
  weightsChanged: boolean;
  onChange: (weights: SkillWeights) => void;
}

const WEIGHT_FIELDS: { key: keyof SkillWeights; label: string }[] = [
  { key: 'strongly_required_skills', label: 'Strongly required' },
  { key: 'required_skills', label: 'Required' },
  { key: 'tools_and_platforms', label: 'Tools and platforms' },
  { key: 'preferred_skills', label: 'Preferred' },
  { key: 'soft_skills', label: 'Soft skills' },
];

export function SkillWeightSettings({
  defaultWeights,
  weights,
  weightsChanged,
  onChange,
}: SkillWeightSettingsProps) {
  const [open, setOpen] = useState(false);

  function updateWeight(key: keyof SkillWeights, value: number) {
    onChange({ ...weights, [key]: value });
  }

  return (
    <div className="weight-settings">
      <div className="weight-settings-heading">
        <div>
          <h3>Admin score override</h3>
          <p>Optionally adjust weights for this match only.</p>
        </div>
        <button className="ghost-button" type="button" onClick={() => setOpen((current) => !current)}>
          {open ? 'Hide weights' : 'Adjust weights'}
        </button>
      </div>

      {open && (
        <div className="weight-settings-body">
          {weightsChanged && <div className="weight-pending-note">Click Calculate match to apply these weights.</div>}
          {WEIGHT_FIELDS.map((field) => (
            <label className="weight-row" key={field.key}>
              <span>{field.label}</span>
              <input
                max={5}
                min={0}
                step={0.5}
                type="range"
                value={weights[field.key]}
                onChange={(event) => updateWeight(field.key, Number(event.target.value))}
              />
              <strong>{weights[field.key].toFixed(1)}</strong>
            </label>
          ))}
          <div className="weight-actions">
            <button className="ghost-button" type="button" onClick={() => onChange(defaultWeights)}>
              Reset to saved defaults
            </button>
            <Link to="/admin/settings">For default weights, aliases, and more settings, go to Settings.</Link>
          </div>
        </div>
      )}
    </div>
  );
}
