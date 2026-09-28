const base = import.meta.env.VITE_API_BASE_URL || '/api';
export async function api<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(base + path, { method: body === undefined ? 'GET' : 'POST', headers: body === undefined ? {} : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(120000) });
  } catch { throw new Error('Unable to reach the workspace. Check your connection and try again.'); }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((e: {loc: string[]; msg: string}) => `${e.loc.slice(1).join(' · ')}: ${e.msg}`).join('. ') : 'Something went wrong. Please try again.');
  }
  return response.json();
}
