import { useState } from 'react';

import type { SkillWeights } from '../types';

export const DEFAULT_SKILL_WEIGHTS: SkillWeights = {
  strongly_required_skills: 3,
  required_skills: 2,
  tools_and_platforms: 1.5,
  preferred_skills: 1,
  soft_skills: 0.5,
};

interface SkillWeightSettingsProps {
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

export function SkillWeightSettings({ weights, weightsChanged, onChange }: SkillWeightSettingsProps) {
  const [open, setOpen] = useState(false);

  function updateWeight(key: keyof SkillWeights, value: number) {
    onChange({
      ...weights,
      [key]: value,
    });
  }

  return (
    <div className="weight-settings">
      <div className="weight-settings-heading">
        <div>
          <h3>Advanced scoring</h3>
          <p>Default score weights are applied. Customize, then calculate again to refresh the score.</p>
        </div>
        <button className="ghost-button" type="button" onClick={() => setOpen((current) => !current)}>
          {open ? 'Hide weights' : 'Customize weights'}
        </button>
      </div>

      {open && (
        <div className="weight-settings-body">
          <div className="weight-defaults-note">
            Default: Strongly required 3.0, Required 2.0, Tools 1.5, Preferred 1.0, Soft skills 0.5
          </div>
          {weightsChanged && (
            <div className="weight-pending-note">
              Custom weights selected. Click Calculate match to refresh the score.
            </div>
          )}
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
          <button className="ghost-button weight-reset-button" type="button" onClick={() => onChange(DEFAULT_SKILL_WEIGHTS)}>
            Reset to defaults
          </button>
        </div>
      )}
    </div>
  );
}
