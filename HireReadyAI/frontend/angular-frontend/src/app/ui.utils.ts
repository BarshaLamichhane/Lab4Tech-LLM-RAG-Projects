export function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function fileFromEvent(event: Event): File | null {
  const input = event.target as HTMLInputElement;
  return input.files?.[0] ?? null;
}

export function textAreaValue(event: Event): string {
  return (event.target as HTMLTextAreaElement).value;
}

export function errorDetail(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'error' in error) {
    const response = error as { error?: { detail?: string } };
    return response.error?.detail || 'Something went wrong.';
  }

  return 'Something went wrong.';
}
