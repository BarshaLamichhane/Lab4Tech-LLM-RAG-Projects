import { ChangeEvent, useEffect, useRef, useState } from 'react';

import { getAdminSettings, matchNewJob, uploadText } from '../api';
import { useAuth } from '../AuthContext';
import type { MatchResponse, SkillWeights } from '../types';
import { errorMessage } from '../ui';
import { NewJobMatchView } from './NewJobMatchView';

export function NewJobMatchPage() {
  const { user } = useAuth();
  const cvTextRef = useRef<HTMLTextAreaElement>(null);
  const jobTextRef = useRef<HTMLTextAreaElement>(null);
  const [saveNewJobProfile, setSaveNewJobProfile] = useState(true);
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');
  const [matchResult, setMatchResult] = useState<MatchResponse | null>(null);
  const [defaultWeights, setDefaultWeights] = useState<SkillWeights>({
    strongly_required_skills: 3,
    required_skills: 2,
    tools_and_platforms: 1.5,
    preferred_skills: 1,
    soft_skills: 0.5,
  });
  const [skillWeights, setSkillWeights] = useState<SkillWeights>(defaultWeights);
  const [weightsChanged, setWeightsChanged] = useState(false);
  const loading = Boolean(loadingLabel);

  useEffect(() => {
    if (user?.role === 'admin') {
      getAdminSettings().then((settings) => {
        setDefaultWeights(settings.skill_weights);
        setSkillWeights(settings.skill_weights);
      }).catch((caughtError) => setError(errorMessage(caughtError)));
    }
  }, []);

  async function readUpload(event: ChangeEvent<HTMLInputElement>, kind: 'cv' | 'job') {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    await runTask(kind === 'cv' ? 'Reading CV file' : 'Reading job description', async () => {
      const text = await uploadText(file, kind);
      if (kind === 'cv' && cvTextRef.current) {
        cvTextRef.current.value = text;
      }
      if (kind === 'job' && jobTextRef.current) {
        jobTextRef.current.value = text;
      }
    });
  }

  async function calculateMatch(includeAllSavedJobs: boolean) {
    const cvText = cvTextRef.current?.value.trim() ?? '';
    const jobDescriptionText = jobTextRef.current?.value.trim() ?? '';
    if (!cvText || !jobDescriptionText) {
      setError('Add a CV and a job description.');
      return;
    }

    await runTask(includeAllSavedJobs ? 'Calculating other fit' : 'Extracting job profile and matching', async () => {
      const result = await matchNewJob(cvText, jobDescriptionText, saveNewJobProfile, includeAllSavedJobs, user?.role === 'admin' ? skillWeights : undefined);
      setMatchResult(result);
      setWeightsChanged(false);
    });
  }

  function updateSkillWeights(weights: SkillWeights) {
    setSkillWeights(weights);
    setWeightsChanged(true);
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
    <NewJobMatchView
      cvTextRef={cvTextRef}
      defaultWeights={defaultWeights}
      error={error}
      jobTextRef={jobTextRef}
      loading={loading}
      loadingLabel={loadingLabel}
      matchResult={matchResult}
      onCalculateMatch={calculateMatch}
      onSaveNewJobProfileChange={setSaveNewJobProfile}
      onSkillWeightsChange={updateSkillWeights}
      onUploadCv={(event) => readUpload(event, 'cv')}
      onUploadJob={(event) => readUpload(event, 'job')}
      saveNewJobProfile={saveNewJobProfile}
      showWeightSettings={user?.role === 'admin'}
      skillWeights={skillWeights}
      weightsChanged={weightsChanged}
    />
  );
}
