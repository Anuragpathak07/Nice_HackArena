<!--
TEMPLATE USAGE
==============
Fill in every {{PLACEHOLDER}} below before use, then delete this comment block.

  {{PROJECT_NAME}}        Human-readable product name, e.g. "Acme Insights"
  {{REPO_NAME}}           Repository name, e.g. "acme-insights-frontend"
  {{APP_TYPE}}            One-line description of the app, e.g. "an internal analytics dashboard"
  {{PRIMARY_USE_CASES}}   Comma list of what it's for, e.g. "sales pipeline tracking, forecasting, and quota management"
  {{ENV_PREFIX}}          Uppercase prefix for env vars, e.g. "ACME"
  {{HOSTING_PLATFORM}}    Deployment target, e.g. "Vercel", "AWS Amplify", "Netlify"
  {{BACKEND_PROJECT_NAME}} Name of a companion backend service, if any (delete §5.8's dev-script line if none)
  {{THEME_STORAGE_KEY}}   localStorage key for theme, e.g. "acme-theme"

The stack listed (Next.js/React/Tailwind/Radix/TanStack Query/Recharts/Framer Motion) is a
sensible default for a modern dashboard app — swap any layer out if your project uses
something else, but keep the *patterns* (RSC boundary, dual-mode API, theme tokens, etc.),
since those are what make this file useful as a standard.
-->

---
name: {{PROJECT_NAME}} Frontend Engineering Standards
description: Standards, patterns, and conventions for developing within the {{REPO_NAME}} repository. Covers the Next.js 15 + React 19 + Tailwind v4 stack, component design patterns, state/API architecture, and best practices.
triggers:
  - When working on {{PROJECT_NAME}} components, pages, or services
  - When creating new UI components, charts, tables, or forms
  - When modifying the API/data layer, mock system, or theme
  - When adding new routes, navigation items, or authentication logic
  - When the user references the {{PROJECT_NAME}} engineering standards or skill guide
---

# {{PROJECT_NAME}} Engineering Standards: Frontend Skill Guide

> **Target Repository**: `{{REPO_NAME}}`
> **Tech Stack**: Next.js 15 (App Router), React 19, Tailwind CSS v4, Radix UI Primitives, TanStack React Query v5, Recharts v3, Framer Motion v12, TypeScript 5.

---

## 1. System Architecture & Core Stack Blueprint

`{{REPO_NAME}}` is {{APP_TYPE}} built for {{PRIMARY_USE_CASES}}.

### Core Stack Matrix

| Architecture Layer | Technology Selection | Configuration & Role |
| :--- | :--- | :--- |
| **Framework** | **Next.js 15** (App Router) | React Server Components (RSC) + Client Components (`"use client"`), `force-dynamic` rendering for authenticated SSR routes. |
| **UI Library** | **React 19** | Concurrent rendering, transitions, hooks (`use`, `useSyncExternalStore`). |
| **Styling Engine** | **Tailwind CSS v4** | `@import "tailwindcss";` directive with CSS inline `@theme` mapping and HSL CSS custom variables. |
| **State & Async** | **TanStack React Query v5** | Server-state caching (`staleTime: 30s`), window focus refetch control, unified query management. |
| **Data Visualization** | **Recharts v3** | Responsive container charts (Area, Bar, Line, Pie) styled via theme CSS variables. |
| **Animations** | **Framer Motion v12** | Micro-interactions, spring-animated numeric values (`useSpring`, `useTransform`), hover gradient overlays. |
| **Primitives** | **Radix UI** | Unstyled, accessible UI components (Dialog, DropdownMenu, Tabs, Tooltip, Select, Accordion, Popover, Switch). |
| **Command Palette** | **cmdk** | ⌘K global command palette for navigation and actions. |
| **Icons** | **Lucide React** | Consistent iconography across the application. |
| **Utilities** | **clsx, tailwind-merge, class-variance-authority** | Conditional class composition and variant APIs. |

> Replace any row above with your project's actual dependency — just keep the "role" column's intent (e.g. if you use Chart.js instead of Recharts, the "wrap charts in a loading boundary, theme via CSS vars" pattern in §3.3 still applies).

### force-dynamic Rendering — Rationale & Scope

The root layout declares `export const dynamic = "force-dynamic"` to ensure every page renders server-side. This is **required** if:

1. **Auth middleware** (`src/middleware.ts`) verifies session cookies on every request. Static optimization would bypass middleware entirely, making all pages publicly accessible without login.
2. **Session state** is read from cookies at request time, so static generation would serve stale auth gates.

**Best practice**: If adding a route that does not need SSR or auth, scope `force-dynamic` to that route's `layout.tsx` or `page.tsx` instead of relying on the blanket default. Public routes (e.g., `/login`) should be explicitly excluded in middleware, but keep in mind that `force-dynamic` at the root means all routes participate in SSR unless explicitly opted out.

> If your app has no auth requirement, drop this rule entirely — it exists specifically to make cookie-gated middleware reliable.

---

## 2. Anti-Flicker Theme System & CSS Design Tokens

### 2.1 Head Script Theme Hydration (`app/layout.tsx`)

Prevents Flash of Unstyled Content (FOUC) by executing a synchronous theme detection script inside `<head>` before page paint:

```typescript
const themeInitScript = `
(function(){
  try {
    var stored = localStorage.getItem('{{THEME_STORAGE_KEY}}');
    var theme = stored === 'light' || stored === 'dark' ? stored : 'light';
    document.documentElement.classList.remove('light','dark');
    document.documentElement.classList.add(theme);
    document.documentElement.style.colorScheme = theme;
  } catch (e) {
    document.documentElement.classList.add('light');
  }
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <QueryProvider>
            <AuthGate>
              <AppShell>{children}</AppShell>
            </AuthGate>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

> Drop `<AuthGate>` from the tree if your app has no login requirement.

### 2.2 Tailwind CSS v4 Theme Mapping (`src/styles/globals.css`)

The token names below are stack-agnostic — reuse the whole block and just swap the color values to match your brand:

```css
@import "tailwindcss";

:root,
html.light {
  --background: #f4f7fb;
  --foreground: #0b1b33;
  --card: rgba(255, 255, 255, 0.78);
  --card-solid: #ffffff;
  --card-foreground: #0b1b33;
  --primary: #1d4ed8;
  --primary-foreground: #f8fbff;
  --secondary: #e8eef8;
  --secondary-foreground: #1e3a5f;
  --muted: #eef3f9;
  --muted-foreground: #5b6f8a;
  --accent: #e3ecf8;
  --accent-foreground: #123056;
  --destructive: #dc2626;
  --border: rgba(15, 40, 80, 0.1);
  --input: rgba(15, 40, 80, 0.12);
  --ring: #3b82f6;
  --success: #059669;
  --warning: #d97706;
  --info: #0284c7;
  --radius: 1rem;
  --sidebar: #0b1b33;
  --sidebar-foreground: #c5d3e6;
  --glow: rgba(37, 99, 235, 0.12);
  --chart-axis: #7b8fa8;
  --chart-grid: rgba(15, 40, 80, 0.08);
  --chart-tooltip-bg: #ffffff;
  --chart-tooltip-border: rgba(15, 40, 80, 0.12);
  --page-bg: #eef1f4;
  --glass-shadow: 0 12px 40px rgba(15, 40, 80, 0.08);
}

html.dark {
  --background: #07111f;
  --foreground: #e8eef6;
  --card: rgba(15, 28, 48, 0.72);
  --card-solid: #0f1c30;
  --card-foreground: #e8eef6;
  --primary: #3b82f6;
  --primary-foreground: #f8fbff;
  --secondary: #15233a;
  --secondary-foreground: #c5d3e6;
  --muted: #132033;
  --muted-foreground: #8fa3bc;
  --accent: #1a2f4d;
  --accent-foreground: #dbe7f5;
  --destructive: #ef4444;
  --border: rgba(148, 163, 184, 0.14);
  --ring: #60a5fa;
  --glow: rgba(59, 130, 246, 0.18);
  --page-bg: #0a1424;
  --glass-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card-solid);
  --color-card-foreground: var(--card-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-border: var(--border);
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", Consolas, monospace;
}

/* Dynamic Glassmorphism Surface Utility */
.glass {
  background: var(--card);
  backdrop-filter: blur(18px);
  border: 1px solid var(--border);
  box-shadow: var(--glass-shadow);
}
```

---

## 3. Advanced UI Component Design Patterns

All components should follow the **RSC + Client boundary** principle: page shells are Server Components, and any interactive/dynamic sub-tree uses `"use client"`. Prefer Radix Primitives for interactive elements and compose them with Tailwind for styling.

### 3.1 Animated Metric KPI Card

Uses Framer Motion springs (`useSpring`, `useTransform`) for physics-based numeric rolling counters on data updates. Note: these hooks come from **Framer Motion**, not React core.

```tsx
"use client";

import { motion, useSpring, useTransform } from "framer-motion";
import { ArrowDownRight, ArrowRight, ArrowUpRight, Minus } from "lucide-react";
import { useEffect } from "react";
import { Badge } from "@/components/shared/badge";
import { Card } from "@/components/shared/card";
import { cn, formatCurrency, formatHours, formatNumber, formatPercent } from "@/lib/utils";
import type { KpiMetric } from "@/types";

function AnimatedValue({ value, format }: { value: number; format: KpiMetric["format"] }) {
  const spring = useSpring(0, { stiffness: 80, damping: 20 });
  const display = useTransform(spring, (latest) => {
    if (format === "percent") return formatPercent(latest);
    if (format === "currency") return formatCurrency(latest);
    if (format === "hours") return formatHours(latest);
    if (format === "number" && value < 2) return formatNumber(latest, 2);
    return formatNumber(latest);
  });

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return <motion.span>{display}</motion.span>;
}

export function KpiCard({ metric }: { metric: KpiMetric }) {
  const TrendIcon =
    metric.trend === "up" ? ArrowUpRight : metric.trend === "down" ? ArrowDownRight : Minus;
  // {{POSITIVE_TREND_RULE}}: for metrics where "down" is good (e.g. cost, cycle time),
  // invert the trend-to-badge mapping like this instead of a flat trend === "up" check.
  const positive =
    metric.lowerIsBetter ? metric.trend === "down" : metric.trend === "up";

  return (
    <Card className="group relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm text-muted-foreground">{metric.label}</p>
          <Badge tone={positive ? "success" : metric.trend === "flat" ? "info" : "warning"}>
            <TrendIcon className="mr-1 h-3 w-3" />
            {metric.delta > 0 ? "+" : ""}
            {metric.format === "number" && metric.value < 2
              ? metric.delta.toFixed(2)
              : `${metric.delta}%`}
          </Badge>
        </div>
        <div className="text-3xl font-semibold tracking-tight">
          <AnimatedValue value={metric.value} format={metric.format} />
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">{metric.hint}</p>
      </div>
    </Card>
  );
}
```

### 3.2 Data Table with Radix

Use Radix Table primitives composed with Tailwind for sortable, paginated data tables. Always include loading and empty states:

```tsx
"use client";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface DataTableProps<T> {
  columns: { key: string; header: string; className?: string }[];
  data: T[];
  loading?: boolean;
  renderRow: (row: T, index: number) => React.ReactNode;
}

export function DataTable<T>({ columns, data, loading, renderRow }: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-border">
        <p className="text-sm text-muted-foreground">No data available.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((col) => (
            <TableHead key={col.key} className={cn("font-medium", col.className)}>
              {col.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>{data.map(renderRow)}</TableBody>
    </Table>
  );
}
```

### 3.3 Chart Component Pattern

Wrap charts in a loading boundary and ensure responsive sizing. Use theme-aware colors via CSS variables so charts adapt automatically to light/dark mode:

```tsx
"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "@/components/ui/skeleton";

interface ChartData {
  label: string;
  value: number;
  secondary?: number;
}

interface DashboardChartProps {
  queryKey: string[];
  queryFn: () => Promise<ChartData[]>;
  dataKey: string;
  secondaryDataKey?: string;
  color: string;
  secondaryColor?: string;
}

export function DashboardChart({
  queryKey,
  queryFn,
  dataKey,
  secondaryDataKey,
  color,
  secondaryColor,
}: DashboardChartProps) {
  const { data, isLoading, error } = useQuery({ queryKey, queryFn, staleTime: 60_000 });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (error) return <EmptyChartState error={error as Error} />;
  if (!data || data.length === 0) return <EmptyChartState />;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
        <XAxis dataKey="label" tick={{ fill: "var(--chart-axis)" }} fontSize={12} />
        <YAxis tick={{ fill: "var(--chart-axis)" }} fontSize={12} />
        <Tooltip contentStyle={{ background: "var(--chart-tooltip-bg)", border: "1px solid var(--chart-tooltip-border)" }} />
        <Area type="monotone" dataKey={dataKey} stroke={color} fill={`url(#gradient-${dataKey})`} strokeWidth={2} />
        {secondaryDataKey && (
          <Area type="monotone" dataKey={secondaryDataKey} stroke={secondaryColor ?? "var(--muted-foreground)"} strokeDasharray="4 4" fill="none" strokeWidth={1.5} />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

### 3.4 Modal / Dialog Composition (Radix)

```tsx
"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  confirmLabel?: string;
  onConfirm?: () => void;
}

export function Modal({ open, onOpenChange, title, description, children, confirmLabel = "Confirm", onConfirm }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className={cn(
            "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg rounded-xl bg-card p-6 shadow-lg",
            "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
          )}
        >
          <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
          {description && <Dialog.Description className="text-sm text-muted-foreground mt-1">{description}</Dialog.Description>}
          <div className="mt-4">{children}</div>
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild><Button variant="outline">Cancel</Button></Dialog.Close>
            {onConfirm && <Button onClick={onConfirm}>{confirmLabel}</Button>}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### 3.5 Form Component Pattern

Use react-hook-form with Zod for validation, composed with your input primitives:

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/shared/form-error";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    // {{AUTH_SUBMIT_LOGIC}} — replace with your actual auth call
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input id="username" {...register("username")} />
        {errors.username && <FormError>{errors.username.message}</FormError>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" {...register("password")} />
        {errors.password && <FormError>{errors.password.message}</FormError>}
      </div>
      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
```

### 3.6 Navigation Shell (SideNav + TopNav + CommandPalette)

The app shell composes three major navigation components:

- **`SideNav`** (`src/components/navigation/side-nav.tsx`): Collapsible sidebar with `useSidebarCollapsed()` hook persisting state to `localStorage`. Uses `NAV_ITEMS` from `src/constants/navigation.ts`.
- **`TopNav`** (`src/components/navigation/top-nav.tsx`): Top bar with scope selector, search, and command palette trigger.
- **`CommandPalette`** (`src/components/navigation/command-palette.tsx`): ⌘K global command palette using `cmdk`.

When building new navigation:
1. Add items to `NAV_ITEMS` in `src/constants/navigation.ts` — never hardcode nav links inline.
2. Use icon components mapped to each `NavItem`.
3. Group items by a `section` field (e.g. `Core`, `Ops` — replace with your own section names).

---

## 4. State Management & API Integration Layer

### 4.1 TanStack Query Client Configuration

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 },
        },
      })
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

**Configuration rationale** — adjust these numbers to your own data's freshness needs:
- `staleTime` prevents unnecessary refetches for data that updates on a slow cadence.
- `refetchOnWindowFocus: false` avoids re-fetching everything when the user tabs back.
- `retry: 1` fails fast and lets the UI handle error states explicitly.

### 4.2 Dual-Mode API Service Pattern

All services in `src/services/api.ts` should follow a dual-mode pattern that switches between live API calls and mock data based on a single flag. This enables fast UI development without a backend:

```typescript
import { API_BASE_URL, USE_MOCK_DATA } from "@/lib/config";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(`API ${path} failed with status ${res.status}`);
  return res.json() as Promise<T>;
}

export const exampleService = {
  async getSummary(query: Record<string, string> = {}): Promise<Summary> {
    if (USE_MOCK_DATA) {
      await new Promise((r) => setTimeout(r, 200));
      return mockSummary;
    }
    const params = new URLSearchParams(query);
    return fetchJson<Summary>(`/summary?${params.toString()}`);
  },
};
```

> Keep this flag in a dedicated config module (e.g. `src/lib/config.ts`), not tucked inside an unrelated constants file — it's easy to lose track of otherwise.

### 4.3 Service Organization

Organize services by domain in `src/services/api.ts`. Example pattern — replace with your own domains:
- `{{domainA}}Service` — e.g. dashboard summaries, trends, insights
- `{{domainB}}Service` — e.g. a specific integration's data
- `{{domainC}}Service` — e.g. user/profile data

When adding a new data source, create a new service object following the same pattern: `async getX()`, mock-first, `fetchJson` fallback.

---

## 5. Standards Checklist & Best Practices

### 5.1 Rendering & Architecture
1. **RSC & Client Directive Boundary**: Keep page shells as Server Components and isolate dynamic interactions inside `"use client"` leaf components. Never mark a whole page as `"use client"` when only a subset needs interactivity.
2. **force-dynamic Scope** (if your app has auth): Opt out per-route only when the route has no auth and no SSR requirements.
3. **Middleware Awareness** (if applicable): Document your public paths (e.g. `/`, `/login`, `/api/auth/*`) and update them when adding unauthenticated routes.

### 5.2 Component Standards
4. **Primitives First**: Use your accessible-primitives library (Radix, etc.) for all interactive elements. Avoid rebuilding these from scratch.
5. **Utility-Only Styling**: Compose primitives with Tailwind classes. Avoid separate CSS files except for global utilities (e.g. `.glass`).
6. **Loading & Error States**: Every data-consuming component must handle three states: loading, error, and empty. §3.2's `DataTable` is the canonical example.
7. **Animated Values**: Import animation hooks (`useSpring`, `useTransform`, etc.) explicitly from your animation library, not confused for framework built-ins.
8. **Component File Naming**: Use PascalCase for component files. Group related components in domain folders under `src/components/`.

### 5.3 Type Safety
9. **Strict TypeScript**: `strict: true` in `tsconfig.json`. No implicit `any`, no unchecked casts.
10. **Type-First Development**: Define types in `src/types/index.ts` before implementing components. Keep API-shape types and UI-shape types' mapping functions in sync.
11. **Path Aliases**: Use `@/` for imports. Avoid relative paths beyond one level up.

### 5.4 State & Data Layer
12. **React Query Patterns**: Use `useQuery` for fetching, `useMutation` for writes. Always provide `queryKey` arrays for cache invalidation.
13. **Mock Data Layer**: A single flag (§4.2) controls whether services return mock data. Document it in one place.
14. **Service Pattern**: Each service method is a single async function that checks the mock flag first, then falls back to a real fetch.

### 5.5 Accessibility
15. **Trust Your Primitives**: Accessible-component libraries provide built-in keyboard nav, focus management, and ARIA. Don't override unless you've verified an improvement.
16. **Semantic HTML**: Use `<main>`, `<nav>`, `<aside>`, `<header>`, `<section>`, `<footer>` appropriately.
17. **Color Contrast**: Verify text-on-background contrast in both themes (aim for ≥4.5:1 for body text).
18. **Focus Visible**: Ensure all interactive elements have a visible focus ring. Test with `Tab` key navigation.

### 5.6 Testing
19. **Unit Tests**: Test hooks, utilities, and mapping functions. Mock the data-mode flag for service tests.
20. **Component Tests**: Test components in all three states (loading, success, error). Verify animations don't block interaction.
21. **Integration Checks**: Verify auth redirects work correctly and SSR routes render with cookies/session intact.

### 5.7 Performance
22. **Bundle Budget**: Set an explicit initial-bundle target (e.g. 200 KB gzipped). Use dynamic imports for heavy, below-the-fold components (charts, command palettes).
23. **Image Optimization**: Use your framework's image component for static assets; prefer SVG icons over raster images.
24. **Query Caching**: Set `staleTime` per query based on how often that data actually changes — don't use one value for everything.
25. **Avoid Waterfalls**: Prefetch likely-next pages/routes where your framework supports it.

### 5.8 Deployment & Environment
26. **{{HOSTING_PLATFORM}} Hosting**: If your app uses SSR/middleware for auth, make sure your hosting tier actually runs a server (not static-only export) — static hosting silently skips middleware and cookie checks.
27. **Environment Variables** (example set — replace with your own):
    - `NEXT_PUBLIC_{{ENV_PREFIX}}_API_BASE` — backend API URL
    - `NEXT_PUBLIC_{{ENV_PREFIX}}_USE_MOCK` — toggle mock/live data
    - `{{ENV_PREFIX}}_AUTH_USER` / `{{ENV_PREFIX}}_AUTH_PASSWORD` / `{{ENV_PREFIX}}_SESSION_SECRET` — auth credentials, if applicable
28. **Concurrent Dev** (if you run a companion backend locally): document the script that runs both, e.g. `dev` runs `{{PROJECT_NAME}}` frontend + `{{BACKEND_PROJECT_NAME}}` backend via `concurrently`.

---

## 6. Quick Reference — Key File Locations

| Purpose | Path |
| :--- | :--- |
| App Router layout | `src/app/layout.tsx` |
| Auth middleware | `src/middleware.ts` |
| Navigation items & config | `src/constants/navigation.ts` |
| Auth helpers & session | `src/lib/auth.ts` |
| Mock data | `src/lib/mock-data.ts` |
| API services | `src/services/api.ts` |
| React Query hooks | `src/hooks/` |
| Theme CSS variables | `src/styles/globals.css` |
| All types | `src/types/index.ts` |
| App routes/pages | `src/app/` |
| Components by domain | `src/components/{domain}/` |
| Shared UI primitives | `src/components/shared/` |
| Deploy config | `{{deploy-config-file, e.g. amplify.yml / vercel.json}}` |

---

## 7. Version Verification Notes

Don't guess package versions from memory or training data — confirm them against your own `package.json` and fill this table in:

| Package | Pinned Version | Notes |
| :--- | :--- | :--- |
| `next` | `{{version}}` | |
| `react` / `react-dom` | `{{version}}` | |
| `@tanstack/react-query` | `{{version}}` | |
| `recharts` | `{{version}}` | Note any major-version API changes if upgrading |
| `framer-motion` | `{{version}}` | |
| `tailwindcss` | `{{version}}` | |
| `@radix-ui/react-*` | `{{version}}` | |
| `typescript` | `{{version}}` | |
