import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, NavLink, Routes, Route, useLocation, Link } from 'react-router-dom';
import { Check, LayoutDashboard, UsersRound, ShieldCheck, History, ArrowUpRight, ChevronRight, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { WorkspaceProvider, useWorkspace } from './store';
import { Overview, Applications, Watchlist, Activity } from './pages';
import { OnboardingPage } from './onboarding';
import { ApplicantDetail } from './detail';
import { Empty, ErrorNotice, Loading } from './components';
import './styles.css';

function App() {
  const { applicants, loading, error, refresh, toast } = useWorkspace();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const pending = applicants.filter(a => a.status === 'PENDING' || a.status === 'IN_REVIEW').length;
  const section = location.pathname.split('/')[1] || 'overview';
  const navigation = [{ path: '/', name: 'Overview', icon: LayoutDashboard }, { path: '/applications', name: 'Applications', icon: UsersRound }, { path: '/watchlist', name: 'Watchlist', icon: ShieldCheck }, { path: '/activity', name: 'Activity log', icon: History }];
  return <div className="app-shell"><a href="#main-content" className="skip-link">Skip to content</a>{mobileOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMobileOpen(false)}/>}
    <aside className={`sidebar ${mobileOpen ? 'is-open' : ''}`}><Link className="brand" to="/" onClick={() => setMobileOpen(false)}><span className="brand-mark"><Check strokeWidth={3} size={22}/></span>clear<span className="brand-period">.</span></Link><div className="workspace-label"><span className="workspace-symbol">C</span><div><strong>Compliance workspace</strong><small>Customer due diligence</small></div></div><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{navigation.map(({ path, name, icon: Icon }) => <NavLink key={path} end={path === '/'} to={path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={18}/><span>{name}</span>{name === 'Applications' && pending > 0 && <span className="nav-count">{pending}</span>}</NavLink>)}</nav><div className="sidebar-bottom"><div className="sidebar-note"><ShieldCheck size={21}/><strong>Clarity at every step.</strong><p>Every finding explained.<br/>Every decision recorded.</p><Link to="/activity">View audit trail <ArrowUpRight size={14}/></Link></div><div className="team-profile"><span className="team-avatar">CT</span><div><strong>Compliance team</strong><small>Review workspace</small></div></div></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setMobileOpen(!mobileOpen)}>{mobileOpen ? <X size={20}/> : <Menu size={20}/>}</button><span>Workspace</span><ChevronRight size={13}/><strong>{section === 'overview' ? 'Overview' : section === 'applications' ? 'Applications' : section === 'watchlist' ? 'Watchlist' : 'Activity log'}</strong>{location.pathname === '/applications/new' && <><ChevronRight size={13}/><span>New application</span></>}</div><div className="topbar-date">{new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</div></header>
    <main id="main-content">{loading ? <Loading/> : error ? <ErrorNotice message={error} retry={() => void refresh()}/> : <Routes><Route path="/" element={<Overview/>}/><Route path="/applications" element={<Applications/>}/><Route path="/applications/new" element={<OnboardingPage/>}/><Route path="/applications/:id" element={<ApplicantDetail/>}/><Route path="/watchlist" element={<Watchlist/>}/><Route path="/activity" element={<Activity/>}/><Route path="*" element={<Empty title="Page not found" text="This page isn’t part of your workspace." action={<Link className="button primary" to="/">Back to overview</Link>}/>}/></Routes>}</main><footer className="workspace-footer"><span>Clear · KYC & AML workspace</span><span>Built for considered decisions</span></footer></div>{toast && <div className="toast" role="status"><Check size={18}/>{toast}</div>}
  </div>;
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><WorkspaceProvider><App/></WorkspaceProvider></BrowserRouter></React.StrictMode>);
