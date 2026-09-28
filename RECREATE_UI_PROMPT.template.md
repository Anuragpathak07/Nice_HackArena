<!--
TEMPLATE USAGE
==============
Fill in every {{PLACEHOLDER}} before feeding this to an AI coding agent.

  {{APP_NAME}}        Generic working name, e.g. "the app" / "Acme"
  {{APP_DOMAIN}}       What the dashboard is about, e.g. "sales analytics", "inventory", "support tickets"
  {{ACCENT_COLOR}}     Your brand's primary accent hex, e.g. #2563eb
  {{KEY_PAGES}}        Your own list of top-level routes (§14 has a starter structure to edit)

This file describes a clean, light SaaS-dashboard aesthetic (Stripe/Vercel/Linear-style) as
a *default* — if your product wants a different visual identity (dark-first, playful,
data-dense enterprise, etc.), rewrite §1's color system and §12's "no dark navy" language
to match. Everything else (layout structure, component list, motion patterns, code
conventions) is aesthetic-agnostic.
-->

# PROMPT: Recreate a {{APP_DOMAIN}} Dashboard UI

Use this prompt when you need to rebuild or redesign a dashboard UI from scratch. Feed the relevant sections to an AI coding agent or design system builder.

---

## OBJECTIVE

Recreate the complete user interface for {{APP_NAME}}, a **{{APP_DOMAIN}} dashboard**. The UI is a clean, modern SaaS platform with a white/light aesthetic, glassmorphism effects, spring-animated transitions, and real-time data visualization. The app is built with **Next.js 15 (App Router), React 19, Tailwind CSS v4, Radix UI, Framer Motion v12, Recharts v3, and TypeScript**.

**Core principle**: The default theme is clean white and light. The sidebar should be white or very light, not dark. The overall feel is a polished, modern SaaS platform — think Stripe dashboard, Vercel Analytics, or Linear. Not a dark-mode military dashboard. *(Swap this description entirely if your product's visual identity is different — see the note at the top of this file.)*

---

## 1. VISUAL IDENTITY & DESIGN TOKENS

### Brand Essence
- **Aesthetic**: Clean, modern SaaS platform. White surfaces, soft accent color, minimal shadows, generous whitespace. Premium but approachable — not intimidating.
- **Vibe**: Light backgrounds, glassmorphism cards with subtle borders, data-driven motion, crisp typography.

### Color System (CSS Custom Properties)

**LIGHT THEME** (default, primary) — clean white surfaces:
- Background: `#ffffff` or `#f8fafc` (off-white)
- Foreground: `#0f172a` (near-black slate)
- Card: `#ffffff` (solid white) or `rgba(255, 255, 255, 0.85)` (subtle glass)
- Primary: `{{ACCENT_COLOR}}` (your brand accent, e.g. `#2563eb`)
- Primary foreground: `#ffffff`
- Secondary: `#e0e7ff` (very soft indigo — tint your accent instead if it's not blue)
- Secondary foreground: `#1e293b`
- Muted: `#f1f5f9` (light gray)
- Muted foreground: `#64748b` (slate gray)
- Accent: `#eff6ff` (pale tint of `{{ACCENT_COLOR}}`)
- Accent foreground: `#1e40af`
- Destructive: `#dc2626`
- Border: `rgba(15, 23, 42, 0.08)` (very subtle dark)
- Ring: `{{ACCENT_COLOR}}` (slightly lighter shade)
- Success: `#16a34a`, Warning: `#d97706`, Info: `#0891b2`
- Page background: `#f8fafc` (soft gray-blue)
- Glass shadow: `0 4px 24px rgba(15, 23, 42, 0.06)`
- Sidebar: `#ffffff` or `#f8fafc` (white or very light)
- Sidebar text: `#334155` (dark slate)

**DARK THEME** (optional second theme):
- Background: `#0f172a`
- Foreground: `#e2e8f0`
- Card: `rgba(30, 41, 59, 0.8)`
- Primary: a lighter tint of `{{ACCENT_COLOR}}` for contrast on dark surfaces
- Muted: `#1e293b`
- Muted foreground: `#94a3b8`
- Border: `rgba(148, 163, 184, 0.12)`

### Typography
- Font sans: `"Inter", ui-sans-serif, system-ui, sans-serif`
- Font mono: `ui-monospace, "SF Mono", Consolas, monospace`
- Use `font-mono` for all numerics, currency, percentages, IDs/hashes
- Heading hierarchy: `text-3xl font-semibold tracking-tight` for page titles, `text-base font-semibold tracking-tight` for card titles, `text-sm text-muted-foreground` for labels, `text-xs leading-relaxed text-muted-foreground` for hints
- Use `tracking-tight` aggressively — tight letter-spacing is a hallmark of clean typography

### Border Radius
- Global: `--radius: 0.75rem` (rounded-lg for most elements)
- Cards: `rounded-2xl` or `rounded-3xl` with glass utility
- Buttons/badges: `rounded-full` or `rounded-xl`
- Input fields: `rounded-xl`

---

## 2. LAYOUT STRUCTURE

### Overall App Shell
Three persistent layout regions visible on all authenticated pages:

```
┌─────────────────────────────────────────────────────────────┐
│  TOP NAV (sticky, z-40, h-auto min-h-16)                    │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│  SIDE    │  MAIN CONTENT AREA                               │
│  NAV     │  ┌────────────────────────────────────────┐      │
│  (64px   │  │  Page title via TopNav                 │      │
│   collapsed│  │  [status strip / filters, if any]      │      │
│   220px  │  │  KPI cards, charts, tables             │      │
│   expanded│  │  Sections, panels, tables              │      │
│   when   │  │  CommandPalette (overlay)              │      │
│   closed)│  │  [floating widget(s), if any]          │      │
│          │  └────────────────────────────────────────┘      │
├──────────┴──────────────────────────────────────────────────┤
│  SIDEBAR FOOTER (collapse toggle)                           │
└─────────────────────────────────────────────────────────────┘
```

### Sidebar Navigation (`SideNav`)
- **Width**: `64px` when collapsed, `220px` when expanded
- **Transition**: `duration-300` with `ease-[cubic-bezier(0.22,1,0.36,1)]`
- **Background**: White or very light (`bg-white` or `bg-slate-50`)
- **Collapsible**: Persists state to `localStorage`
- **Layout**:
  - Top: Logo / app name text — small, clean, no heavy branding image
  - Middle: Navigation items grouped by category (replace with your own sections, e.g. "Main", "Reports", "Settings")
  - Bottom: Collapse toggle button
- **Active state**: `bg-blue-50 text-primary font-medium` (subtle accent highlight — swap `blue` for your accent color's Tailwind scale)
- **Inactive state**: `text-slate-500 hover:bg-slate-100 hover:text-slate-900`
- **Collapsed mode**: Icons only, centered, with tooltip on hover
- **Nav item styling**: `flex items-center rounded-lg text-[14px] font-medium tracking-tight transition-colors`, `gap-2.5 px-3 py-2` when expanded

### Top Navigation (`TopNav`)
- **Position**: `sticky top-0 z-40`, `min-h-16`, `px-4 py-3 sm:px-6`
- **Background**: White or very light, with a subtle bottom border
- **Left section**:
  - Page title — `text-lg font-semibold tracking-tight sm:text-xl`
  - Optional status indicator (small colored dot or pill)
  - Optional scope/filter selector (dropdown for team, project, date range — only if your app has multi-scope data)
- **Right section** (items gap-2 sm:gap-3):
  1. **Search bar**: `flex max-w-xs min-w-[160px] rounded-full border border-slate-200 bg-slate-100 px-3 py-2`, search icon + "Search…" placeholder
  2. **Command palette trigger (⌘K)**: `h-8 w-8 rounded-full`, `border border-slate-200 bg-slate-100`, centered ⌘ symbol
  3. **Theme toggle** (light/dark switch) — subtle icon
  4. **Notifications bell** — small icon button, if applicable
  5. **Sign out button**: `h-8 w-8 rounded-full`, icon only
  6. **User avatar**: `h-8 w-8 rounded-full flex items-center justify-center text-[11px] font-semibold`, tinted background using your accent color, initials (2-3 letters)

### Main Content Area
- Container: `flex-1 flex-col p-3 pl-0` inside the shell
- Scrollable main: `overflow-y-auto px-4 py-6 sm:px-6 lg:px-8`
- Page header: `mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between` — `h1.sr-only` for title, description paragraph (`text-sm text-slate-500 sm:text-base`), optional actions
- Page-level content uses `motion.div` with `initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}`

---

## 3. COMPONENT LIBRARY

### Card
- Base: `bg-white rounded-2xl p-5 border border-slate-100 shadow-sm transition-all duration-200 hover:border-blue-200 hover:shadow-md` (swap `blue` for your accent)
- Sub-components: `CardHeader` (`mb-3 flex items-start justify-between gap-2`), `CardTitle` (`text-sm font-semibold tracking-tight text-slate-900`), `CardDescription` (`text-xs text-slate-500`)

### Badge
- Base: `inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium`
- Tones: `default` (`bg-slate-100 text-slate-600`), `success` (`bg-green-50 text-green-700`), `warning` (`bg-amber-50 text-amber-700`), `risk` (`bg-red-50 text-red-700`), `info` (`bg-blue-50 text-blue-700`)

### Button
- `rounded-full` pills, primary variant with your accent color background + white text
- Secondary variant: `bg-slate-100 text-slate-700 border border-slate-200`
- Hover states with smooth transitions; disabled states with `opacity-50`

### Skeleton
- `animate-pulse rounded-xl bg-slate-100` — used for loading states across all data-consuming components

### Tabs
- Radix `Tabs` with `TabsList`, `TabsTrigger`, `TabsContent`. Active tab: tinted with your accent color.

### Modal / Dialog
- Radix `Dialog` composed with Tailwind. White modal, `rounded-2xl shadow-xl`. Backdrop: `bg-black/40`. Smooth open/close animations.

### Tooltip
- Radix `Tooltip` with custom trigger. Small pill: `bg-slate-900 text-white text-xs rounded-md px-2 py-1`.

---

## 4. DASHBOARD COMPONENTS

Everything below is generic dashboard vocabulary — rename to match your own domain's key metrics.

### KPI Card
- White card with subtle border, rounded-2xl padding
- Small area-chart sparkline (`AreaChart`, `Area`, `ResponsiveContainer`)
- Label: `uppercase tracking-[0.06em] text-[11px] font-semibold text-slate-400`
- Value: `text-2xl font-bold text-slate-900`
- Trend indicator: colored up/down arrow with percentage
- Hover: subtle shadow increase + border color change
- Optional benchmark badge and/or short insight text (`text-xs text-slate-500`)

### Metric Sparkline Card
- Card-based layout with area chart, gradient fill matching stroke color
- Label + large value (`text-2xl font-bold`) + subtitle
- Chart area: `h-16 w-full` responsive container
- Optional health indicator (check/warning icon)

### Hero Metric Card
- Large hero card for your single most important number
- Value + trend + comparison to a baseline
- Optional: horizontal timeline/breakdown of stages or sub-components, each a colored bar segment, with an "expand for detail" affordance

### Status Strip
- Horizontal strip showing current data-source status (e.g. live/mock/hybrid), small colored dots, compact and unobtrusive

### Entity/Team Panel
- Grid or list of cards for people, teams, or accounts — avatar with initials, name, metric summary, small status badge

### Data Table
- `rounded-xl overflow-hidden border border-slate-200`
- Header row: `bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500`
- Data rows: hover `bg-slate-50`; trend indicators in cells where relevant
- Pagination at bottom

### Metrics Panel
- A set of domain-specific benchmark metrics, each showing a large value + benchmark badge + health indicator (replace with whatever your product's core KPIs are, e.g. NPS/churn/latency/conversion)

### Notifications / Activity Feed
- List of items: timestamp, title, description; subtle left-border accent color by severity

### Section Navigation
- Tab-style navigation for dashboard sub-sections; `bg-slate-100` container, `rounded-lg`, active tab `bg-white text-slate-900 shadow-sm`

---

## 5. NAVIGATION & SEARCH

### Command Palette
- Global overlay triggered by ⌘K or search button
- Full-width modal overlay centered, search input at top, lists navigation items as commands
- Keyboard navigation (arrow keys, Enter); `cmdk` library
- Animated open/close (`zoom-in-95` / `zoom-out-95`)

### Sidebar Navigation
- See §2 for details. Active route highlighted with your accent color; separator between sections (`my-2 border-t border-slate-100`); collapse button in footer; tooltip on collapsed items.

### Theme Toggle
- Light/dark, persisted to `localStorage` via a context provider

### Search
- Search button in top nav opens command palette; shows `Search…` + `⌘K` hint; results include navigation links and, if relevant, recent items

---

## 6. AI / ASSISTANT COMPONENTS *(optional — delete this section if your product has no AI feature)*

### Assistant Widget
- Floating action button (FAB) in bottom-right corner, accent-colored or outlined, `h-12 w-12`
- Opens a chat panel (docked or modal); backdrop click closes it; animates open/close

### Assistant Panel
- Chat-style interface with message bubbles, session management, citations if RAG-backed, scope-aware if your app has multi-scope data

### Summary/Digest Panel
- Slide-out panel for an AI-generated summary, `rounded-2xl bg-white shadow-xl`

---

## 7. AUTH & ACCESS CONTROL *(delete/adjust if your app has no auth)*

### Login Page
- Full-page centered sign-in form, clean white background, app name at top
- Fields: `rounded-xl border border-slate-200 px-4 py-3`
- Primary button: accent-colored, `rounded-xl py-3 font-medium`
- Redirects to your main authenticated route after login

### Auth Gate
- Wraps all authenticated content; checks session on mount; loading state (spinner or "Loading…"); unauthenticated → redirect to `/login`
- Document your public paths explicitly (e.g. `/`, `/login`, `/login/*`)

### User Avatar
- Initials in a colored circle, tinted with your accent color, `rounded-full`, `h-8 w-8` or `h-9 w-9`

---

## 8. STATE MANAGEMENT

### Scope / Filter Provider *(if your data is multi-tenant/multi-scope)*
- Context with current scope (team, project, user, date range) and setters

### React Query Setup
- `staleTime: 30_000` as a default (adjust per query type)
- `refetchOnWindowFocus: false`
- `retry: 1`
- Query keys organized by domain

---

## 9. DATA VISUALIZATION PATTERNS

### Chart Library Usage
- `ResponsiveContainer` wrapping all charts
- `AreaChart` for sparklines and trend charts
- `CartesianGrid` with a light gray stroke
- Axis ticks in muted-foreground color, `fontSize={11}`
- Tooltip with white background, subtle border, `borderRadius: 8px`
- Gradient fills matching the series' stroke color
- Dashed lines (`strokeDasharray="4 4"`) for comparison series

### Chart Color System
Define a fixed palette so charts stay consistent across the app — example:

| Color | Hex | Usage |
|-------|-----|-------|
| {{ACCENT_COLOR}} | — | Primary metric, main data line |
| Green | `#16a34a` | Healthy/positive indicators |
| Amber | `#d97706` | Warnings, attention-needed |
| Cyan | `#0891b2` | Secondary metric |
| Rose | `#f43f5e` | Negative trends, errors |
| Indigo | `#6366f1` | Additional data series |

---

## 10. ANIMATION & MOTION DESIGN

### Motion Patterns
- **Page entrance**: `motion.div` with `initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}`
- **KPI value animation**: `useSpring(0, { stiffness: 80, damping: 20 })` + `useTransform` for spring-physics numeric rolling counters
- **Hover effects**: `group-hover:shadow-md`, `group-hover:border-[accent]-200`
- **Sidebar transition**: `transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]`
- **Tooltip animation**: `opacity-0 translate-y-1 scale-95` → `translate-y-0 scale-100 opacity-100`, `duration-150 ease-out`
- **Modal/dialog**: `zoom-in-95` / `zoom-out-95`
- **Skeleton pulse**: `animate-pulse`

### Easing Curves
- Sidebar slide: `cubic-bezier(0.22, 1, 0.36, 1)`
- KPI animation: stiffness 80, damping 20
- Hover transitions: `duration-150 ease-out`
- Page transitions: `duration: 0.3`

---

## 11. THEME SYSTEM

### Light/Dark Toggle
- `ThemeProvider` context with `theme`, `setTheme`, `toggleTheme`, `mounted`
- Persists to `localStorage` under an app-specific key
- Applies via `document.documentElement.classList.add(theme)` and `document.documentElement.style.colorScheme = theme`
- Theme init script runs synchronously in `<head>` to prevent FOUC

### Tailwind v4 Configuration
- `@import "tailwindcss"` at top of `globals.css`
- `@theme inline` block mapping CSS variables to Tailwind utilities
- All colors use CSS custom properties from `:root` and `html.dark`
- `--radius: 0.75rem` for global border radius
- Clean, minimal shadow values (no heavy dark shadows in light mode)

---

## 12. MICRO-INTERACTIONS & DETAILS

### Hover Effects
- Cards: `hover:border-[accent]-200 hover:shadow-md`
- Nav items: `hover:bg-slate-100 hover:text-slate-900`
- Buttons: `hover:opacity-90`, `hover:shadow-sm`
- Search bar: `hover:border-slate-300 hover:bg-white`
- Table rows: `hover:bg-slate-50`

### Focus States
- `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[accent]-500` on all interactive elements

### Loading States
- `Skeleton` components with `animate-pulse`
- Simple text fallbacks acceptable for small widgets: `isLoading ? <p className="text-sm text-slate-400">Loading…</p>`
- Error states: `isError ? <p className="text-sm text-amber-600">…</p>`

### Badges & Status Indicators
- Status dots: green (live), amber (mock/degraded), blue (hybrid) — or your own semantics
- Trend indicators: colored `↑` / `↓` / `→` arrows
- Health icons: `✓` (healthy), `⚠` (warning)

---

## 13. RESPONSIVE DESIGN

### Breakpoints
- `sm:` (640px): Search text hidden, adjusted padding
- `md:` (768px): grid adjustments
- `lg:` (1024px): increased padding
- `xl:` (1280px): full multi-column layouts

### Responsive Patterns
- Sidebar collapses on smaller screens or via user toggle
- Top nav wraps: `flex-wrap items-center justify-between gap-2`
- Page header: `flex-col gap-3 sm:flex-row sm:items-end sm:justify-between`
- KPI grid: `grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4`
- Text labels hidden on small screens where they don't add value

---

## 14. KEY PAGES TO BUILD

Replace this list with {{KEY_PAGES}} — your own app's actual top-level routes. Example starter structure for a typical SaaS dashboard:

### Dashboard (`/dashboard`)
- Status strip at top (if applicable)
- Hero metric card
- KPI grid: metric cards × 4 (1 column on mobile, 2 on sm, 4 on xl)
- Fade-in animation on mount; loading/error states

### [Your primary detail/report view] (`/{{route}}`)
- Metric sparkline cards in a grid
- Progress/goal indicators
- Notifications or activity feed

### [Your secondary domain view] (`/{{route}}`)
- Domain-specific insight cards
- Trend charts
- Health/status indicators per item

### [Your metrics deep-dive] (`/metrics/...`)
- Metrics panel(s) with sub-navigation for categories
- Optional comparison filter toggle

### Settings (`/settings`)
- Application configuration, theme preferences, auth settings

### Login (`/login`) *(if applicable)*
- Full-page centered sign-in form, clean branding at top, redirect after auth

---

## 15. CODE CONVENTIONS

### File Structure
```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout with ThemeProvider, QueryProvider, AuthGate
│   ├── page.tsx
│   ├── login/
│   ├── dashboard/
│   ├── {{your-other-routes}}/
│   ├── settings/
│   ├── api/
│   └── ...
├── components/
│   ├── shared/             # Card, Badge, Button, Skeleton, Tabs, Modal, Tooltip
│   ├── layout/              # AppShell, PageHeader
│   ├── navigation/          # SideNav, TopNav, CommandPalette, ThemeToggle
│   ├── dashboard/           # Dashboard-specific components
│   ├── auth/                # AuthGate
│   └── {{domain}}/          # One folder per business domain
├── hooks/                   # useDashboard, useDataSource, useSidebarCollapsed, etc.
├── services/                 # api.ts (all data services)
├── lib/                      # auth.ts, mock-data.ts, utils, config
├── types/                    # index.ts (all TypeScript types)
├── constants/                 # navigation.ts (NAV_ITEMS, etc.)
└── styles/                    # globals.css
```

### Import Conventions
- Use `@/` alias for all imports
- `"use client"` directive at the top of every client component
- Named exports for all components

### Component Pattern
```tsx
"use client";

import { /* ... */ } from "react";
import { /* ... */ } from "@/components/ui/*";
import { cn } from "@/lib/utils";
import type { /* ... */ } from "@/types";

export function ComponentName({ /* props */ }) {
  return (
    <div className={cn("base-classes", className)}>
      {/* ... */}
    </div>
  );
}
```

---

## 16. IMPORTANT NOTES

1. **This is meant to be a real, production-quality build** — don't simplify or approximate spacing, colors, typography, or animations unless you've said so.
2. **White/light is the default theme** in this template — the sidebar should be white or very light, not dark navy, *unless you've overridden §1's color system for a different visual identity.*
3. **Glassmorphism is used sparingly** — subtle `bg-white/85` glass cards on light backgrounds, not heavy blur effects, by default.
4. **All charts use theme-aware CSS variables** — not hardcoded colors — so they adapt to light/dark automatically.
5. **Spring/animation hooks (`useSpring`/`useTransform` or equivalent) come from your animation library** — they are not framework built-ins. Import explicitly.
6. **Name your actual charting/animation/primitives libraries** in place of the defaults here if your stack differs — the layout and interaction patterns still apply.
7. **The mock/live toggle is controlled by a single flag** — when true, all API calls return realistic mock data with artificial delay, so the UI can be built and demoed without a backend.
8. **The theme system must prevent FOUC** — the inline script in `<head>` runs before paint.
9. **`force-dynamic` rendering** (or your framework's equivalent) is needed for authenticated routes if middleware does server-side cookie verification.
10. **No brand-specific names in the generated code** unless you provide them — use generic "App" naming until you fill in {{APP_NAME}}.
11. **The color palette should feel intentional, not default-Tailwind** — pick an accent and derive tints/shades from it consistently, rather than mixing arbitrary blues/grays.
