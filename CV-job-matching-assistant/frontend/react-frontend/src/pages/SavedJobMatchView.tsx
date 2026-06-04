import { ChangeEvent, RefObject } from 'react';

import { MatchResult } from '../components/MatchResult';
import { SkillWeightSettings } from '../components/SkillWeightSettings';
import type { MatchResponse, SkillWeights } from '../types';

interface SavedJobMatchViewProps {
  cvTextRef: RefObject<HTMLTextAreaElement | null>;
  error: string;
  loading: boolean;
  loadingLabel: string;
  matchResult: MatchResponse | null;
  onCalculateMatch: (includeAllSavedJobs: boolean) => void;
  onRefreshRoles: () => void;
  onSelectedRoleChange: (role: string) => void;
  onSkillWeightsChange: (weights: SkillWeights) => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  roles: string[];
  selectedRole: string;
  skillWeights: SkillWeights;
  weightsChanged: boolean;
}

export function SavedJobMatchView({
  cvTextRef,
  error,
  loading,
  loadingLabel,
  matchResult,
  onCalculateMatch,
  onRefreshRoles,
  onSelectedRoleChange,
  onSkillWeightsChange,
  onUploadCv,
  roles,
  selectedRole,
  skillWeights,
  weightsChanged,
}: SavedJobMatchViewProps) {
  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Saved Job Match</p>
          <h1>Compare a candidate CV against an existing extracted job</h1>
        </div>
        <button className="ghost-button" type="button" onClick={onRefreshRoles}>
          Refresh roles
        </button>
      </section>

      <section className="input-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>Candidate CV</h2>
            <label className="file-control">
              <span>Upload</span>
              <input type="file" accept=".txt,.pdf,application/pdf,text/plain" onChange={onUploadCv} />
            </label>
          </div>
          <textarea ref={cvTextRef} spellCheck={false} />
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Target role</h2>
            <span className="count">{roles.length} saved</span>
          </div>
          <select value={selectedRole} onChange={(event) => onSelectedRoleChange(event.target.value)}>
            <option value="" disabled>
              Select a saved role
            </option>
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <SkillWeightSettings weights={skillWeights} weightsChanged={weightsChanged} onChange={onSkillWeightsChange} />
          <button className="primary-button action-gap" type="button" disabled={loading} onClick={() => onCalculateMatch(false)}>
            Calculate match
          </button>
          <button className="ghost-button full-width action-gap" type="button" disabled={loading || !matchResult} onClick={() => onCalculateMatch(true)}>
            Show other fit
          </button>
        </div>
      </section>

      {(loading || error) && (
        <section className="status-row">
          {loading && <div className="status loading">{loadingLabel}...</div>}
          {error && <div className="status error">{error}</div>}
        </section>
      )}

      {matchResult && <MatchResult result={matchResult} />}
    </>
  );
}
