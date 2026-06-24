import type { MatchResponse } from '../types';
import { downloadJson } from '../ui';
import { MatchResultView } from './MatchResultView';

interface MatchResultProps {
  result: MatchResponse;
}

export function MatchResult({ result }: MatchResultProps) {
  return (
    <MatchResultView
      result={result}
      onDownload={() => downloadJson(result, 'cv-match-result.json')}
    />
  );
}
