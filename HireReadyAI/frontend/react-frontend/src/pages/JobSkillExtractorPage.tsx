import { ChangeEvent, useRef, useState } from 'react';

import { extractJobSkills, uploadText } from '../api';
import type { ExtractJobSkillsResponse } from '../types';
import { downloadJson, errorMessage } from '../ui';
import { JobSkillExtractorView } from './JobSkillExtractorView';

export function JobSkillExtractorPage() {
  const jobTextRef = useRef<HTMLTextAreaElement>(null);
  const [saveJobProfile, setSaveJobProfile] = useState(true);
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');
  const [extractionResult, setExtractionResult] = useState<ExtractJobSkillsResponse | null>(null);
  const loading = Boolean(loadingLabel);

  async function uploadJobDescription(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    await runTask('Reading job description', async () => {
      const text = await uploadText(file, 'job');
      if (jobTextRef.current) {
        jobTextRef.current.value = text;
      }
    });
  }

  async function extractSkills() {
    const jobDescriptionText = jobTextRef.current?.value.trim() ?? '';
    if (!jobDescriptionText) {
      setError('Add a job description.');
      return;
    }

    await runTask('Extracting job skills', async () => {
      const result = await extractJobSkills(jobDescriptionText, saveJobProfile);
      setExtractionResult(result);
    });
  }

  async function runTask(label: string, task: () => Promise<void>) {
    setError('');
    setLoadingLabel(label);
    try {
      await task();
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    } finally {
      setLoadingLabel('');
    }
  }

  return (
    <JobSkillExtractorView
      error={error}
      extractionResult={extractionResult}
      jobTextRef={jobTextRef}
      loading={loading}
      loadingLabel={loadingLabel}
      onDownload={() => {
        if (extractionResult) {
          downloadJson(extractionResult.job_profile, 'job-profile.json');
        }
      }}
      onExtractSkills={extractSkills}
      onSaveJobProfileChange={setSaveJobProfile}
      onUploadJob={uploadJobDescription}
      saveJobProfile={saveJobProfile}
    />
  );
}
