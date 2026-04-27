export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') return data.detail;
    if (typeof data?.message === 'string') return data.message;
    return JSON.stringify(data).slice(0, 240);
  } catch {
    try {
      return (await response.text()).slice(0, 240);
    } catch {
      return 'Yanıt okunamadı';
    }
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: 'no-store' });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(`API GET ${path} failed: ${response.status} ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store',
  });
  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(`API POST ${path} failed: ${response.status} ${detail}`);
  }
  return response.json() as Promise<T>;
}
