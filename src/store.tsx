import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api } from './api';
import type { Applicant, WatchEntry, Audit } from './types';
interface Store { applicants: Applicant[]; watchlist: WatchEntry[]; audits: Audit[]; loading: boolean; error: string; refresh: () => Promise<void>; notify: (message: string) => void; toast: string; }
const WorkspaceContext = createContext<Store>(null!);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [applicants, setApplicants] = useState<Applicant[]>([]);
  const [watchlist, setWatchlist] = useState<WatchEntry[]>([]);
  const [audits, setAudits] = useState<Audit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, notify] = useState('');
  const refresh = useCallback(async () => {
    try {
      const [a, w, l] = await Promise.all([api<Applicant[]>('/workspace/applications'), api<WatchEntry[]>('/watchlist?limit=1000'), api<Audit[]>('/audit-logs')]);
      setApplicants(a); setWatchlist(w); setAudits(l); setError('');
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (toast) { const id = setTimeout(() => notify(''), 5000); return () => clearTimeout(id); } }, [toast]);
  return <WorkspaceContext.Provider value={{ applicants, watchlist, audits, loading, error, refresh, notify, toast }}>{children}</WorkspaceContext.Provider>;
}
export const useWorkspace = () => useContext(WorkspaceContext);
