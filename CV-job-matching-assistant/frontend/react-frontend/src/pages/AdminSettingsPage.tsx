import { useEffect, useState } from 'react';

import { getAdminSettings, updateAdminSettings } from '../api';
import type { AppSettings, SkillWeights } from '../types';
import { errorMessage } from '../ui';

const WEIGHT_LABELS: { key: keyof SkillWeights; label: string }[] = [
  { key: 'strongly_required_skills', label: 'Strongly required skills' },
  { key: 'required_skills', label: 'Required skills' },
  { key: 'tools_and_platforms', label: 'Tools and platforms' },
  { key: 'preferred_skills', label: 'Preferred skills' },
  { key: 'soft_skills', label: 'Soft skills' },
];

export function AdminSettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [skillAliases, setSkillAliases] = useState('');
  const [broadAliases, setBroadAliases] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const loaded = await getAdminSettings();
      setSettings(loaded);
      setSkillAliases(JSON.stringify(loaded.skill_aliases, null, 2));
      setBroadAliases(JSON.stringify(loaded.broad_skill_aliases, null, 2));
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  async function save() {
    if (!settings) return;
    setError('');
    setStatus('');
    try {
      const saved = await updateAdminSettings({
        ...settings,
        skill_aliases: JSON.parse(skillAliases),
        broad_skill_aliases: JSON.parse(broadAliases),
      });
      setSettings(saved);
      setStatus('Settings saved. New matches now use these defaults.');
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  function updateWeight(key: keyof SkillWeights, value: number) {
    if (!settings) return;
    setSettings({
      ...settings,
      skill_weights: { ...settings.skill_weights, [key]: value },
    });
  }

  if (!settings) {
    return <section className="status-row"><div className="status loading">Loading admin settings...</div></section>;
  }

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Matching settings</h1>
        </div>
      </section>
      <section className="settings-grid">
        <div className="panel">
          <h2>Default score weights</h2>
          <p className="muted-line">These weights apply to all regular-user matches.</p>
          <div className="admin-weight-grid">
            {WEIGHT_LABELS.map(({ key, label }) => (
              <label key={key}>
                <span>{label}</span>
                <input className="number-input" min={0} step={0.5} type="number" value={settings.skill_weights[key]} onChange={(event) => updateWeight(key, Number(event.target.value))} />
              </label>
            ))}
          </div>
        </div>
        <div className="panel">
          <h2>Skill aliases</h2>
          <p className="muted-line">Map CV terms to canonical skills using JSON.</p>
          <textarea className="settings-editor" spellCheck={false} value={skillAliases} onChange={(event) => setSkillAliases(event.target.value)} />
        </div>
        <div className="panel settings-wide">
          <h2>Broad skill aliases</h2>
          <p className="muted-line">Define broad skills and the specific skills that should match them.</p>
          <textarea className="settings-editor" spellCheck={false} value={broadAliases} onChange={(event) => setBroadAliases(event.target.value)} />
        </div>
      </section>
      <section className="status-row">
        {status && <div className="status loading">{status}</div>}
        {error && <div className="status error">{error}</div>}
        <button className="primary-button settings-save" type="button" onClick={save}>Save settings</button>
      </section>
    </>
  );
}
