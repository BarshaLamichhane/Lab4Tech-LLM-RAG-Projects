import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { changePassword, getUserLLMSettings, updateUserLLMSettings } from '../api';
import { useAuth } from '../AuthContext';
import type { UserLLMSettings } from '../types';
import { errorMessage } from '../ui';

const MISTRAL_MODELS = [
  'mistral-large-latest',
  'mistral-medium-latest',
  'mistral-small-latest',
  'ministral-8b-latest',
];
const OPENAI_MODELS = ['gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini', 'gpt-4o'];

export function AccountPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [llmSettings, setLlmSettings] = useState<UserLLMSettings | null>(null);
  const [provider, setProvider] = useState<UserLLMSettings['provider']>('mistral');
  const [modelName, setModelName] = useState('mistral-large-latest');
  const [apiKey, setApiKey] = useState('');
  const [clearApiKey, setClearApiKey] = useState(false);
  const [llmStatus, setLlmStatus] = useState('');
  const [error, setError] = useState('');
  const [llmError, setLlmError] = useState('');
  const [loading, setLoading] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);

  useEffect(() => {
    getUserLLMSettings()
      .then((settings) => {
        setLlmSettings(settings);
        setProvider(settings.provider);
        setModelName(settings.model_name);
      })
      .catch((caughtError) => setLlmError(errorMessage(caughtError)));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (newPassword !== confirmation) {
      setError('New passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      await logout();
      navigate('/login', { replace: true });
    } catch (caughtError) {
      setError(errorMessage(caughtError));
    } finally {
      setLoading(false);
    }
  }

  async function saveLlmSettings(event: FormEvent) {
    event.preventDefault();
    setLlmError('');
    setLlmStatus('');
    setLlmLoading(true);
    try {
      const saved = await updateUserLLMSettings({
        provider,
        modelName,
        apiKey,
        clearApiKey,
      });
      setLlmSettings(saved);
      setApiKey('');
      setClearApiKey(false);
      setLlmStatus('LLM settings saved. New extraction and interview requests will use these settings.');
    } catch (caughtError) {
      setLlmError(errorMessage(caughtError));
    } finally {
      setLlmLoading(false);
    }
  }

  return (
    <>
      <section className="topbar">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Security settings</h1>
        </div>
      </section>
      <section className="auth-shell account-shell">
        <form className="panel auth-panel" onSubmit={submit}>
          <h2>Change password</h2>
          <p className="muted-line">Signed in as {user?.username}. Changing your password signs out existing sessions.</p>
          <label className="field-label" htmlFor="current-password">Current password</label>
          <input id="current-password" className="number-input" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} />
          <label className="field-label" htmlFor="new-password">New password</label>
          <input id="new-password" className="number-input" minLength={12} type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} />
          <label className="field-label" htmlFor="confirm-password">Confirm new password</label>
          <input id="confirm-password" className="number-input" minLength={12} type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
          {error && <div className="status error">{error}</div>}
          <button className="primary-button action-gap" disabled={loading} type="submit">
            {loading ? 'Updating password...' : 'Update password'}
          </button>
        </form>
        <form className="panel auth-panel" onSubmit={saveLlmSettings}>
          <h2>LLM provider</h2>
          <p className="muted-line">Use the server default key or add your own Mistral key. Existing keys are never shown back in full.</p>

          <label className="field-label" htmlFor="llm-provider">Provider</label>
          <select id="llm-provider" className="number-input" value={provider} onChange={(event) => {
            const nextProvider = event.target.value as UserLLMSettings['provider'];
            setProvider(nextProvider);
            setModelName(nextProvider === 'openai' ? OPENAI_MODELS[0] : MISTRAL_MODELS[0]);
          }}>
            <option value="mistral">Mistral</option>
            <option value="openai">OpenAI</option>
          </select>

          <label className="field-label" htmlFor="llm-model">Model</label>
          <select id="llm-model" className="number-input" value={modelName} onChange={(event) => setModelName(event.target.value)}>
            {(provider === 'openai' ? OPENAI_MODELS : MISTRAL_MODELS).map((model) => <option key={model} value={model}>{model}</option>)}
          </select>
          <input
            className="number-input"
            placeholder={`Or type another ${provider === 'openai' ? 'OpenAI' : 'Mistral'} model name`}
            value={modelName}
            onChange={(event) => setModelName(event.target.value)}
          />

          <label className="field-label" htmlFor="llm-api-key">{provider === 'openai' ? 'OpenAI' : 'Mistral'} API key</label>
          <input
            id="llm-api-key"
            className="number-input"
            placeholder={llmSettings?.has_api_key ? `Current key: ${llmSettings.api_key_preview}` : 'Leave empty to use server default'}
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
          />
          <label className="check-row">
            <input type="checkbox" checked={clearApiKey} onChange={(event) => setClearApiKey(event.target.checked)} />
            <span>Clear my saved API key and use server default</span>
          </label>
          {llmSettings?.has_api_key && <p className="muted-line">Saved key: {llmSettings.api_key_preview}</p>}
          {llmStatus && <div className="status loading">{llmStatus}</div>}
          {llmError && <div className="status error">{llmError}</div>}
          <button className="primary-button action-gap" disabled={llmLoading} type="submit">
            {llmLoading ? 'Saving LLM settings...' : 'Save LLM settings'}
          </button>
        </form>
      </section>
    </>
  );
}
