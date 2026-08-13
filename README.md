# Project & Team Task Manager

A full-stack task management application with multi-organization support, role-based permissions, and per-project task tracking.

## Table of Contents
1. [How to Run](#1-how-to-run)
2. [Data Model & Roles](#2-data-model--roles)
3. [Technical Decisions](#3-technical-decisions)
4. [Trade-offs](#4-trade-offs)
5. [What I'd Do Differently](#5-what-id-do-differently)
6. [Difficulties Encountered](#6-difficulties-encountered)
7. [Design Q&A](#7-design-qa)

---

## 1. How to Run

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env if needed (default values work for local dev)

# Run migrations
python manage.py migrate

# (Optional) Run tests
python manage.py test

# Start the dev server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env from example
cp .env.example .env

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Environment Variables

**Backend** (``backend/.env``):
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-insecure | Django secret key |
| `DEBUG` | True | Debug mode |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | Allowed hosts |
| `CORS_ALLOWED_ORIGINS` | http://localhost:5173 | CORS origins |
| `SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | 15 | Access token TTL |
| `SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS` | 7 | Refresh token TTL |
| `DRF_THROTTLE_ANON` | 5/min | Anonymous rate limit |
| `DRF_THROTTLE_USER` | 30/min | Authenticated rate limit |

**Frontend** (``frontend/.env``):
| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | http://localhost:8000/api | Backend API URL |

---

## 2. Data Model & Roles

### Entity Relationship

```
User (AbstractUser)
 ├── Membership → Organization (many-to-many through Membership)
 ├── Organization.created_by → User
 ├── Project.created_by → User
 └── Task.assignee → User (nullable)
     Task.created_by → User

Organization
 ├── Membership (user, role) — unique_together(user, organization)
 └── Project (organization FK)

Project
 └── Task (project FK)
     ActivityLog (task FK) — [extra: audit trail]

Task
 ├── fields: title, description, status, priority, assignee, due_date
 └── created_by, created_at, updated_at
```

### Roles

| Role | Permissions |
|------|-------------|
| **OWNER** | Everything an ADMIN can do, plus: cannot be demoted/removed (last owner protection) |
| **ADMIN** | Create/edit/delete projects, manage members (add/remove/change roles), edit/delete any task |
| **MEMBER** | Create tasks, edit/delete own tasks, change status of own/assigned tasks |
| **VIEWER** | Read-only access to organization data (projects, tasks, members) |

### Task Edit Rules (Documented)

- The **creator** (`created_by`) of a task or an **ADMIN/OWNER** of the organization can edit or reassign it.
- The **creator**, **assignee**, or an **ADMIN/OWNER** can change the task status.
- A `VIEWER` cannot create, edit, or delete tasks.
- An assignee must be a member of the task's organization (validated in the serializer).

---

## 3. Technical Decisions

### Authentication: JWT with SimpleJWT

**Choice:** JWT (access + refresh tokens) via `djangorestframework-simplejwt`, with token blacklist on logout.

**Rationale:** The frontend is a SPA on a separate origin (Vite dev server at :5173, API at :8000). JWT is stateless and works cleanly with CORS without needing a cookie-based session. The access token is short-lived (15 min) and the refresh token is rotated on each refresh. The blacklist app ensures that refresh tokens used for logout are invalidated server-side.

**Alternative considered:** DRF's built-in Token auth. Simpler (single token per user, no refresh needed), but it requires a DB lookup on every request and doesn't support fine-grained token lifecycle. For a SPA with transparent refresh, JWT is the better fit.

### Roles: Enum Field on Membership

**Choice:** A `role` CharField with 4 choices on the `Membership` model, enforced through permission classes and `perform_*` methods.

**Rationale:** 4 roles don't justify a separate Role model or a permissions bitfield. The `unique_together(user, organization)` constraint ensures one membership per user per org. Role checks are done both at the view level (permission_classes) and the object level (in `perform_create/update/destroy` and `get_queryset`).

### ViewSets vs API Views

- **Organizations/Members/Projects/Tasks:** ViewSets with explicit mixins. DRF's router generates clean nested URLs (`/organizations/{slug}/members/`). Using `SimpleRouter` instead of `DefaultRouter` avoids the root API view conflicting with organization detail URLs.
- **Auth (register/login/me/logout):** `APIView`/`generics.CreateAPIView`. Auth endpoints have non-standard response shapes (tokens vs user objects) and benefit from explicit control over the response structure.

### Permission Strategy

Permissions are enforced at **three layers**:

1. **Queryset-level (`get_queryset`):** `OrganizationViewSet.get_queryset()` filters to only orgs where the user has a `Membership`. `TaskViewSet` and `ProjectViewSet` filter by org membership. This prevents cross-organization data leakage — even if a user guesses an ID, the queryset won't include it, returning 404.

2. **View-level (`permission_classes`):** `IsAuthenticated` on all endpoints. `IsOrganizationAdmin` for member-management endpoints.

3. **Object-level (`perform_*`):** In each viewset's `perform_create`, `perform_update`, `perform_destroy`, the user's role is checked against the business rules before allowing the action. This catches cases where queryset filtering alone isn't enough (e.g., a MEMBER trying to create a project in an org they belong to but don't have admin rights for).

### Frontend Architecture

```
src/
├── api/         — Centralized HTTP client (client.js) + per-domain modules
├── context/     — AuthContext (session state, login/logout/refreshUser)
├── components/  — Reusable UI (Layout, Spinner, ErrorBanner, EmptyState, ConfirmDialog, Pagination)
├── pages/       — Route-level pages (Login, Register, OrganizationList, OrganizationDetail, ProjectDetail, NotFound)
└── styles/      — Global CSS (single file, CSS variables for theming)
```

**No UI libraries.** All components are hand-built with CSS variables and vanilla CSS. `react-router-dom` is the only non-React dependency.

---

## 4. Trade-offs

### localStorage vs Cookies for JWT
**Chosen:** localStorage.

**Pros:** Simple to implement in a SPA; no CSRF concerns; easy to clear on logout.
**Cons:** Vulnerable to XSS — if an attacker can inject JavaScript, they can read the token. In a production app, I'd use httpOnly secure cookies with a SameSite attribute, which would require a CSRF token and a backend that sets/clears cookies. This is the biggest security trade-off in the project.

### Server-side vs Client-side Pagination
**Chosen:** Server-side pagination (DRF PageNumberPagination, 20 items/page).

**Pros:** Consistent payload sizes; works with large datasets; the API returns `count`, `next`, `previous` metadata.
**Cons:** Extra round-trips on page change. For a task manager where lists rarely exceed a few hundred items, this is fine. If lists grew to thousands, I'd add infinite scroll or cursor-based pagination.

### SimpleRouter vs DefaultRouter
**Chosen:** `SimpleRouter` for nested routers.

**Rationale:** `DefaultRouter` generates a root API view at the prefix path (e.g., `/organizations/{slug}/`) which conflicts with the organization detail endpoint. `SimpleRouter` omits this, allowing clean nesting without URL conflicts.

### Monolith vs Microservices
**Chosen:** Django monolith with a React SPA.

The spec says "no microservices." A monolith is the right choice for this scope: one codebase, one deployment, shared auth/permissions logic.

---

## 5. What I'd Do Differently

**Priority 1:** **Move JWT to httpOnly cookies.** This is the most impactful security improvement. Use a CSRF token for mutation requests. This makes the token invisible to XSS scripts, at the cost of added complexity.

**Priority 2:** **Add optimistic concurrency control to tasks.** Currently, two users editing the same task could silently overwrite each other. I'd add an `updated_at` field-based optimistic lock: the client sends `If-Match: <timestamp>` and the server rejects the update if the timestamp differs.

**Priority 3:** **Real-time notifications via WebSocket (Django Channels).** When a task's status changes or a user is assigned, notify all org members in real time. This would require adding Channels, Redis as a channel layer, and a WebSocket client in the frontend.

**Priority 4:** **Activity log UI.** The backend already has the `summary` endpoint and the data model supports an activity log. I'd add a timeline view in the project detail page showing recent changes (task created, status changed, reassigned).

**Priority 5:** **Comprehensive frontend tests.** Add Vitest + React Testing Library tests for the UI, covering critical flows (login → create org → add member → create project → create task → change status). Currently only the backend has automated tests.

---

## 6. Difficulties Encountered

1. **URL routing conflict with nested routers.** Using `DefaultRouter` for nested resources (e.g., `organizations/{slug}/members/`) generated a root API view at `organizations/{slug}/` that intercepted requests meant for the `OrganizationViewSet` detail endpoint. The symptom: PATCH to update an org returned 405 (Method Not Allowed) instead of 200/403, and unauthenticated users got 200 instead of 404. **Fix:** Switched to `SimpleRouter` and reordered urlpatterns so the main router is included before the nested one.

2. **Custom User model must be set before first migration.** Setting `AUTH_USER_MODEL = 'accounts.User'` in settings means Django can't even run `manage.py check` without the model existing. I had to create the accounts app (with the User model) before the scaffold could boot. **Fix:** Created the accounts app and User model as part of the initial scaffold, then fleshed out the endpoints in the next commit.

3. **DRF filter backend defaults.** Setting `DEFAULT_FILTER_BACKENDS` globally to include `DjangoFilterBackend` caused issues on endpoints that don't have defined `filterset_fields`. **Fix:** Only declared `filter_backends` on the `TaskViewSet` where filters are needed, and kept the global setting for consistency.

4. **JWT refresh deduplication on the frontend.** When multiple API calls fail with 401 simultaneously, each could trigger a separate refresh request, causing race conditions and token desynchronization. **Fix:** Added a singleton `refreshPromise` in `client.js` that deduplicates concurrent refresh requests — all 401-retry calls wait on the same promise.

---

## 7. Design Q&A

### a. How would you avoid N+1 when listing tasks with assignee and project in a single response?

Use `select_related` for FKs (single-value relationships) and `prefetch_related` for reverse FKs (multi-value):

```python
Task.objects.filter(project_id=pid) \
    .select_related("assignee", "created_by", "project", "project__organization") \
    .prefetch_related("project__organization__memberships")
```

`select_related` uses a SQL JOIN, so all data is fetched in a single query. `prefetch_related` fires a second query with `IN (...)` for the reverse relation. In the current implementation, the `TaskViewSet.get_queryset()` already uses `select_related("assignee", "created_by", "project", "project__organization")`, so listing tasks makes exactly 1 query.

### b. If the task list grows to tens of thousands per organization, what would you change?

**API:**
- Switch from offset-based to **cursor-based pagination** (DRF's `CursorPagination`). Offset pagination with `LIMIT/OFFSET` degrades at deep pages because the DB scans and discards all preceding rows. Cursor pagination uses `WHERE created_at < ?` with an index, which is O(1) regardless of depth.
- Add **compound database indexes** on `(project_id, status)`, `(project_id, assignee_id)`, and `(project_id, created_at)` to optimize filtered+ordered queries.
- Consider **read replicas** for the task list endpoint if the write load is high.

**Frontend:**
- Replace pagination with **virtualized infinite scroll** (e.g., `react-window` or `@tanstack/react-virtual`). Only render visible rows.
- Debounce the search input (already done) and cache filter results.
- Use `staleTime` in a query cache (e.g., TanStack Query) to avoid refetching on every navigation.

### c. Where would you validate "don't assign tasks to non-members": serializer, model, signal, or domain service, and why?

**In the serializer** (which is where it's implemented now). Rationale:

- **Serializer:** Has access to both the request context (`self.context["request"]`, `self.context["project"]`) and can return a 400 JSON response with a clear field-level error. This is the right layer for API input validation because it integrates naturally with DRF's validation pipeline.
- **Model (`clean()`):** Would work, but `clean()` is not called automatically on `save()` unless you call `full_clean()`, and DRF doesn't call it by default. It also doesn't have request context, making it harder to determine which org the task belongs to.
- **Signal (`pre_save`):** Fires on every save, including management commands and data migrations. It's invisible and hard to test. It also throws exceptions, which the API layer would need to catch and format — pushing presentation logic into model-layer code.
- **Domain service:** Overkill for this scope. A service layer adds indirection without benefit in a CRUD-style app where the serializer already has full context.

The key principle: validate at the **boundary** (serializer/API) where you have both input context and can produce user-friendly errors. Reserve model-level validation for invariants that must hold regardless of how the model is accessed.

### d. A plausible race condition (two users editing the same task) and how you'd mitigate it at the middleware level.

**Scenario:** User A and User B both open Task #42. User A changes the title to "Fix login bug" and saves. User B (who loaded the page before A's save) changes the status to "DONE" and saves. User B's PATCH overwrites the title back to the old value because B's payload was constructed from stale data.

**Mitigation with optimistic locking:**

Add an `updated_at` (or a dedicated `version` integer) to the `Task` model. The client sends the `updated_at` it loaded in an `If-Match` header (or as `expected_updated_at` in the body). The view checks:

```python
class TaskViewSet(ModelViewSet):
    def perform_update(self, serializer):
        expected = self.request.headers.get("If-Match")
        if expected and str(serializer.instance.updated_at.isoformat()) != expected:
            raise Conflict("This task was modified by another user. Please refresh.")
        serializer.save()
```

The DB-level query would be: `UPDATE tasks SET ... WHERE id = ? AND updated_at = ?`, and if `affected_rows == 0`, return 409 Conflict. This ensures no silent overwrites and the loser gets a clear error.

For a more robust solution, use `SELECT ... FOR UPDATE` inside a transaction to serialize concurrent writes, but optimistic locking is usually sufficient for UI-driven edits.

### e. If real-time notifications were needed tomorrow, what piece would you touch first and what would you leave out of scope initially?

**Touch first:**
- **Backend:** Add `djangochannels` (ASGI) and a Redis channel layer. Create a consumer that authenticates the WebSocket with the JWT and subscribes the user to a group named `org-{org_slug}`. When a task is created/updated/deleted, send a message to the org's group from within the viewset (e.g., `async_to_sync(channel_layer.group_send)(...)`). The message contains the task ID, action type, and a minimal payload.
- **Frontend:** Add a WebSocket client in `AuthContext` (or a dedicated `RealtimeContext`) that connects on login and dispatches events to update the task list in-place. No re-fetch needed — just patch the local state.

**Leave out of scope initially:**
- **Presence indicators** ("User is typing..."). Adds complexity (debouncing, heartbeats) but little value for a task manager.
- **Push notifications (mobile/browser).** Requires service workers and permission flows; not needed for an MVP.
- **Multi-user cursors or field-level locks.** Operational-transform/CRDT-level complexity; wait until the app proves it needs this.
- **Message persistence/history.** Store events in the activity log (which already exists), but don't build a full chat backend. The WebSocket is ephemeral; the activity log is the source of truth.

---

## API Endpoints Summary

| Method | Endpoint | Permission |
|--------|----------|------------|
| POST | `/api/auth/register/` | Anonymous (5/min) |
| POST | `/api/auth/login/` | Anonymous (5/min) |
| POST | `/api/auth/token/refresh/` | Refresh token |
| POST | `/api/auth/logout/` | Authenticated |
| GET | `/api/auth/me/` | Authenticated |
| GET | `/api/organizations/` | Authenticated (own orgs) |
| POST | `/api/organizations/` | Authenticated |
| GET | `/api/organizations/{slug}/` | Org member |
| PATCH | `/api/organizations/{slug}/` | Org admin |
| GET | `/api/organizations/{slug}/members/` | Org member |
| POST | `/api/organizations/{slug}/members/` | Org admin |
| PATCH | `/api/organizations/{slug}/members/{id}/` | Org admin |
| DELETE | `/api/organizations/{slug}/members/{id}/` | Org admin |
| GET | `/api/organizations/{slug}/projects/` | Org member |
| POST | `/api/organizations/{slug}/projects/` | Org admin |
| GET | `/api/projects/{id}/` | Org member |
| PATCH | `/api/projects/{id}/` | Org admin |
| DELETE | `/api/projects/{id}/` | Org admin |
| GET | `/api/projects/{id}/summary/` | Org member |
| GET | `/api/projects/{id}/tasks/` | Org member |
| POST | `/api/projects/{id}/tasks/` | Member+ (not Viewer) |
| GET | `/api/tasks/{id}/` | Org member |
| PATCH | `/api/tasks/{id}/` | Creator or Admin/Owner |
| DELETE | `/api/tasks/{id}/` | Creator or Admin/Owner |
| PATCH | `/api/projects/{id}/tasks/{id}/change-status/` | Creator/Assignee/Admin/Owner |

## Tests

40 backend tests covering:
- Auth: registration, duplicate email, password mismatch, login, me endpoint
- Organization permissions: cross-org visibility, member vs admin, auto-owner on creation
- Membership: admin-only management, cannot demote owner, cannot remove last owner
- Project permissions: member/viewer cannot create, admin/owner can, outsider blocked
- Task permissions: viewer cannot create, assignee validation, creator-only edit, status change rules
- Task filters: by status, by priority, search by title, pagination metadata

Run tests: `cd backend && python manage.py test`