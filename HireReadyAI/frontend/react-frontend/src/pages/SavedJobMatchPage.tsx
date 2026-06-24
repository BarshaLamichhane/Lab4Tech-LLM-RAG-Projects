import { ChangeEvent, useEffect, useRef, useState } from 'react';

import { getAdminSettings, getRoles, matchSavedJob, uploadText } from '../api';
import { useAuth } from '../AuthContext';
import type { MatchResponse, SkillWeights } from '../types';
import { errorMessage } from '../ui';
import { SavedJobMatchView } from './SavedJobMatchView';

export function SavedJobMatchPage() {
  const { user } = useAuth();
  const cvTextRef = useRef<HTMLTextAreaElement>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('');
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
    refreshRoles();
    if (user?.role === 'admin') {
      getAdminSettings().then((settings) => {
        setDefaultWeights(settings.skill_weights);
        setSkillWeights(settings.skill_weights);
      }).catch((caughtError) => setError(errorMessage(caughtError)));
    }
  }, []);

  async function refreshRoles() {
    try {
      const loadedRoles = await getRoles();
      setRoles(loadedRoles);
      setSelectedRole((currentRole) => currentRole || loadedRoles[0] || '');
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    }
  }

  async function uploadCv(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    await runTask('Reading CV file', async () => {
      const text = await uploadText(file, 'cv');
      if (cvTextRef.current) {
        cvTextRef.current.value = text;
      }
    });
  }

  async function calculateMatch(includeAllSavedJobs: boolean) {
    const cvText = cvTextRef.current?.value.trim() ?? '';
    if (!cvText || !selectedRole) {
      setError('Add a CV and choose a target role.');
      return;
    }

    await runTask(includeAllSavedJobs ? 'Calculating other fit' : 'Calculating match', async () => {
      const result = await matchSavedJob(cvText, selectedRole, includeAllSavedJobs, user?.role === 'admin' ? skillWeights : undefined);
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
    <SavedJobMatchView
      cvTextRef={cvTextRef}
      defaultWeights={defaultWeights}
      error={error}
      loading={loading}
      loadingLabel={loadingLabel}
      matchResult={matchResult}
      onCalculateMatch={calculateMatch}
      onRefreshRoles={refreshRoles}
      onSelectedRoleChange={setSelectedRole}
      onSkillWeightsChange={updateSkillWeights}
      onUploadCv={uploadCv}
      roles={roles}
      selectedRole={selectedRole}
      showWeightSettings={user?.role === 'admin'}
      skillWeights={skillWeights}
      weightsChanged={weightsChanged}
    />
  );
}
