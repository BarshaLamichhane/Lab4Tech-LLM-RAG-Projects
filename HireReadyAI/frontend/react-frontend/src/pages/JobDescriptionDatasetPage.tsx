import { useMemo, useState } from 'react';

import { createJobDescriptionEvaluationCase } from '../api';
import type { JobDescriptionEvaluationDatasetRequest, JobDescriptionEvaluationDatasetResponse } from '../types';
import { errorMessage } from '../ui';

type ListField =
  | 'strongly_required_skills'
  | 'required_skills'
  | 'preferred_skills'
  | 'soft_skills'
  | 'tools_and_platforms'
  | 'experience'
  | 'responsibilities';

const EMPTY_FORM: JobDescriptionEvaluationDatasetRequest = {
  filename: '',
  saved_profile_file: '',
  role: '',
  company_name: '',
  company_context: '',
  industry_domain: '',
  business_problem: '',
  strongly_required_skills: [],
  required_skills: [],
  preferred_skills: [],
  soft_skills: [],
  tools_and_platforms: [],
  experience: [],
  responsibilities: [],
};

const LIST_FIELDS: Array<{ key: ListField; label: string; hint: string }> = [
  {
    key: 'responsibilities',
    label: 'Responsibilities',
    hint: 'One responsibility per line.',
  },
  {
    key: 'strongly_required_skills',
    label: 'Strongly required skills',
    hint: 'Must-have skills only. No verbatim quote needed.',
  },
  {
    key: 'required_skills',
    label: 'Required skills',
    hint: 'Required capability areas, one per line.',
  },
  {
    key: 'preferred_skills',
    label: 'Preferred skills',
    hint: 'Nice-to-have skills, one per line.',
  },
  {
    key: 'soft_skills',
    label: 'Soft skills',
    hint: 'Communication, collaboration, ownership, and similar traits.',
  },
  {
    key: 'tools_and_platforms',
    label: 'Tools and platforms',
    hint: 'Concrete tools, platforms, frameworks, databases, and cloud services.',
  },
  {
    key: 'experience',
    label: 'Experience',
    hint: 'Years, seniority, or production-experience requirements.',
  },
];

export function JobDescriptionDatasetPage() {
  const [form, setForm] = useState<JobDescriptionEvaluationDatasetRequest>(EMPTY_FORM);
  const [listText, setListText] = useState<Record<ListField, string>>({
    strongly_required_skills: '',
    required_skills: '',
    preferred_skills: '',
    soft_skills: '',
    tools_and_platforms: '',
    experience: '',
    responsibilities: '',
  });
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [savedCase, setSavedCase] = useState<JobDescriptionEvaluationDatasetResponse | null>(null);

  const preview = useMemo(() => buildPreviewJson(form), [form]);
  const canSave = form.role.trim().length > 0;

  function updateField(key: keyof JobDescriptionEvaluationDatasetRequest, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateListField(key: ListField, value: string) {
    setListText((current) => ({ ...current, [key]: value }));
    setForm((current) => ({ ...current, [key]: parseLines(value) }));
  }

  async function save() {
    setError('');
    setStatus('');
    setSavedCase(null);
    try {
      const saved = await createJobDescriptionEvaluationCase(form);
      setSavedCase(saved);
      setStatus('Evaluation dataset entry saved.');
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  function reset() {
    setForm(EMPTY_FORM);
    setListText({
      strongly_required_skills: '',
      required_skills: '',
      preferred_skills: '',
      soft_skills: '',
      tools_and_platforms: '',
      experience: '',
      responsibilities: '',
    });
    setStatus('');
    setError('');
    setSavedCase(null);
  }

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Admin evaluation</p>
          <h1>Job-description dataset builder</h1>
          <p className="muted-line">Create evaluation job-description samples using the same fields as the Mistral extraction schema.</p>
        </div>
      </section>

      <section className="evaluation-builder-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <h2>Dataset entry</h2>
              <p className="muted-line">Saved as JSON into `evaluation/job_descriptions` and `evaluation/expected_job_skills.json`.</p>
            </div>
          </div>

          <div className="input-grid">
            <label>
              <span className="field-label">Filename</span>
              <input value={form.filename} placeholder="ai_engineer_role.json" onChange={(event) => updateField('filename', event.target.value)} />
            </label>
            <label>
              <span className="field-label">Saved Mistral profile file</span>
              <input value={form.saved_profile_file} placeholder="ai_engineer_lab4tech_2026.json" onChange={(event) => updateField('saved_profile_file', event.target.value)} />
            </label>
            <label>
              <span className="field-label">Role</span>
              <input value={form.role} placeholder="AI Engineer" onChange={(event) => updateField('role', event.target.value)} />
            </label>
            <label>
              <span className="field-label">Company name</span>
              <input value={form.company_name} placeholder="Lab4Tech" onChange={(event) => updateField('company_name', event.target.value)} />
            </label>
          </div>

          <label>
            <span className="field-label">Company context</span>
            <textarea className="short-textarea" value={form.company_context} placeholder="Short description of what the company does." onChange={(event) => updateField('company_context', event.target.value)} />
          </label>
          <div className="input-grid">
            <label>
              <span className="field-label">Industry domain</span>
              <input value={form.industry_domain} placeholder="AI learning and automation" onChange={(event) => updateField('industry_domain', event.target.value)} />
            </label>
            <label>
              <span className="field-label">Business problem</span>
              <input value={form.business_problem} placeholder="Helping candidates prepare for role-specific interviews" onChange={(event) => updateField('business_problem', event.target.value)} />
            </label>
          </div>

          <div className="dataset-section-grid">
            {LIST_FIELDS.map((field) => (
              <label key={field.key}>
                <span className="field-label">{field.label}</span>
                <small className="muted-line">{field.hint}</small>
                <textarea className="dataset-list-textarea" value={listText[field.key]} onChange={(event) => updateListField(field.key, event.target.value)} />
              </label>
            ))}
          </div>

          <section className="status-row">
            {status && <div className="status loading">{status}</div>}
            {error && <div className="status error">{error}</div>}
          </section>

          {savedCase && (
            <div className="next-step-panel">
              <div>
                <strong>{savedCase.case_id}</strong>
                <span>{savedCase.job_description_file}</span>
              </div>
              <div>
                <strong>Expected labels updated</strong>
                <span>{savedCase.expected_job_skills_file}</span>
              </div>
            </div>
          )}

          <div className="button-row">
            <button className="ghost-button" type="button" onClick={reset}>Reset</button>
            <button className="primary-button" type="button" disabled={!canSave} onClick={save}>Save evaluation dataset</button>
          </div>
        </div>

        <aside className="panel dataset-preview-panel">
          <h2>JSON file preview</h2>
          <p className="muted-line">This is what will be written into the job-description sample JSON file.</p>
          <pre>{preview}</pre>
        </aside>
      </section>
    </>
  );
}

function parseLines(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(/\r?\n/)
        .map((line) => line.replace(/^[-*]\s*/, '').trim())
        .filter(Boolean),
    ),
  );
}

function buildPreviewJson(form: JobDescriptionEvaluationDatasetRequest): string {
  return JSON.stringify({
    role: form.role,
    company_name: form.company_name,
    company_context: form.company_context,
    industry_domain: form.industry_domain,
    business_problem: form.business_problem,
    strongly_required_skills: form.strongly_required_skills,
    required_skills: form.required_skills,
    preferred_skills: form.preferred_skills,
    soft_skills: form.soft_skills,
    tools_and_platforms: form.tools_and_platforms,
    experience: form.experience,
    responsibilities: form.responsibilities,
  }, null, 2);
}
