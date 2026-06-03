import { ChangeEvent, RefObject } from 'react';

import { MatchResult } from '../components/MatchResult';
import type { MatchResponse } from '../types';

interface NewJobMatchViewProps {
  cvTextRef: RefObject<HTMLTextAreaElement | null>;
  error: string;
  jobTextRef: RefObject<HTMLTextAreaElement | null>;
  loading: boolean;
  loadingLabel: string;
  matchResult: MatchResponse | null;
  onCalculateMatch: (includeAllSavedJobs: boolean) => void;
  onSaveNewJobProfileChange: (saveNewJobProfile: boolean) => void;
  onUploadCv: (event: ChangeEvent<HTMLInputElement>) => void;
  onUploadJob: (event: ChangeEvent<HTMLInputElement>) => void;
  saveNewJobProfile: boolean;
}

export function NewJobMatchView({
  cvTextRef,
  error,
  jobTextRef,
  loading,
  loadingLabel,
  matchResult,
  onCalculateMatch,
  onSaveNewJobProfileChange,
  onUploadCv,
  onUploadJob,
  saveNewJobProfile,
}: NewJobMatchViewProps) {
  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">New Job Match</p>
          <h1>Compare a candidate CV with a newly uploaded job description</h1>
        </div>
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
            <h2>Job description</h2>
            <label className="file-control">
              <span>Upload</span>
              <input type="file" accept=".txt,text/plain" onChange={onUploadJob} />
            </label>
          </div>
          <textarea ref={jobTextRef} spellCheck={false} />

          <label className="check-row">
            <input type="checkbox" checked={saveNewJobProfile} onChange={(event) => onSaveNewJobProfileChange(event.target.checked)} />
            <span>Save extracted profile</span>
          </label>
          <button className="primary-button" type="button" disabled={loading} onClick={() => onCalculateMatch(false)}>
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
