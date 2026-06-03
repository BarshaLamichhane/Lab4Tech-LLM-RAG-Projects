import { ChangeEvent, useEffect, useRef, useState } from 'react';

import { getRoles, matchSavedJob, uploadText } from '../api';
import type { MatchResponse } from '../types';
import { errorMessage } from '../ui';
import { SavedJobMatchView } from './SavedJobMatchView';

export function SavedJobMatchPage() {
  const cvTextRef = useRef<HTMLTextAreaElement>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');
  const [matchResult, setMatchResult] = useState<MatchResponse | null>(null);
  const loading = Boolean(loadingLabel);

  useEffect(() => {
    refreshRoles();
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
      const result = await matchSavedJob(cvText, selectedRole, includeAllSavedJobs);
      setMatchResult(result);
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
    <SavedJobMatchView
      cvTextRef={cvTextRef}
      error={error}
      loading={loading}
      loadingLabel={loadingLabel}
      matchResult={matchResult}
      onCalculateMatch={calculateMatch}
      onRefreshRoles={refreshRoles}
      onSelectedRoleChange={setSelectedRole}
      onUploadCv={uploadCv}
      roles={roles}
      selectedRole={selectedRole}
    />
  );
}
