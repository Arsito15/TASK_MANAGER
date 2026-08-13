# Frontend

React SPA for the Task Manager application. Built with Vite, vanilla CSS, and `react-router-dom`. No UI libraries.

## Structure

```
src/
├── api/           — Centralized HTTP client + per-domain modules
│   ├── client.js    — apiRequest/apiCall with JWT, auto-refresh on 401, normalized errors
│   ├── auth.js      — register, login, logout, getMe
│   ├── organizations.js — CRUD for orgs + members
│   ├── projects.js  — CRUD for projects + summary endpoint
│   └── tasks.js    — CRUD for tasks + change-status
├── context/       — React context
│   └── AuthContext.jsx — session state (user, login, logout, refreshUser)
├── components/     — Reusable UI
│   ├── Layout.jsx    — app header + page container + logout
│   ├── Spinner.jsx   — animated loading indicator
│   ├── ErrorBanner.jsx — API error display
│   ├── EmptyState.jsx  — empty list placeholder
│   ├── ConfirmDialog.jsx — modal for delete/remove confirmations
│   └── Pagination.jsx  — server-side pagination controls
├── pages/          — Route-level pages
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── OrganizationList.jsx  — user's orgs + create new
│   ├── OrganizationDetail.jsx — members (add/role/remove) + projects
│   ├── ProjectDetail.jsx     — task list with filters, pagination, summary counters, CRUD
│   └── NotFound.jsx
└── styles/
    └── global.css  — design system (CSS variables, Manrope font, components)
```

## How to run

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Or with Docker (from project root): `make up`

Frontend available at `http://localhost:5173`.

## Key features

- **Protected routes**: unauthenticated users redirected to `/login`
- **JWT auth**: tokens in localStorage, auto-refresh on 401 with dedup
- **Role-aware UI**: buttons hidden/shown based on `my_role` (VIEWER read-only, MEMBER can create, ADMIN/OWNER can manage)
- **Task filters**: by status, priority, and title search (server-side)
- **Pagination**: server-side (DRF PageNumberPagination, 20 items/page)
- **Summary counters**: project page shows TODO/IN_PROGRESS/DONE totals
- **Assignee dropdown**: lists org members instead of raw IDs