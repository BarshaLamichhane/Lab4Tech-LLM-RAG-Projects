import { ChangeEvent, RefObject } from 'react';
import { Link } from 'react-router-dom';

import type { ExtractJobSkillsResponse } from '../types';

interface JobSkillExtractorViewProps {
  error: string;
  extractionResult: ExtractJobSkillsResponse | null;
  jobTextRef: RefObject<HTMLTextAreaElement | null>;
  loading: boolean;
  loadingLabel: string;
  onDownload: () => void;
  onExtractSkills: () => void;
  onSaveJobProfileChange: (saveJobProfile: boolean) => void;
  onUploadJob: (event: ChangeEvent<HTMLInputElement>) => void;
  saveJobProfile: boolean;
}

export function JobSkillExtractorView({
  error,
  extractionResult,
  jobTextRef,
  loading,
  loadingLabel,
  onDownload,
  onExtractSkills,
  onSaveJobProfileChange,
  onUploadJob,
  saveJobProfile,
}: JobSkillExtractorViewProps) {
  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Job Skill Extractor</p>
          <h1>Generate structured skills JSON from a job description</h1>
        </div>
      </section>

      <section className="input-grid single-input">
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
            <input type="checkbox" checked={saveJobProfile} onChange={(event) => onSaveJobProfileChange(event.target.checked)} />
            <span>Save extracted profile</span>
          </label>
          <button className="primary-button" type="button" disabled={loading} onClick={onExtractSkills}>
            Extract skills
          </button>
        </div>
      </section>

      {(loading || error) && (
        <section className="status-row">
          {loading && <div className="status loading">{loadingLabel}...</div>}
          {error && <div className="status error">{error}</div>}
        </section>
      )}

      {extractionResult && (
        <section className="panel json-panel">
          <div className="panel-heading">
            <h2>Extracted job profile</h2>
            <button className="ghost-button" type="button" onClick={onDownload}>
              Download JSON
            </button>
          </div>
          <div className="next-step-panel">
            <div>
              <strong>Want to check fit for this role?</strong>
              <span>Compare a CV with the saved extracted job role.</span>
            </div>
            <Link to="/saved-job-match">Go to CV matcher</Link>
            <div>
              <strong>Want to practise for interview?</strong>
              <span>Use the saved role in interview preparation mode.</span>
            </div>
            <Link to="/interview-practice">Go to interview practice</Link>
          </div>
          {extractionResult.saved_path && <p>Saved at {extractionResult.saved_path}</p>}
          <pre>{JSON.stringify(extractionResult.job_profile, null, 2)}</pre>
        </section>
      )}
    </>
  );
}
