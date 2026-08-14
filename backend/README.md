# Backend

Django + DRF API for the Task Manager application. JWT authentication, role-based permissions, and per-organization data isolation.

## Apps

```
apps/
├── accounts/        — Custom User model + auth endpoints
│   ├── models.py      — User (AbstractUser, email as USERNAME_FIELD)
│   ├── views.py       — RegisterView, LoginView, MeView, LogoutView
│   ├── serializers.py — RegisterSerializer (password validation), UserSerializer
│   └── tests.py       — registration, duplicate email, login, me (6 tests)
│
├── organizations/   — Organization + Membership (roles)
│   ├── models.py      — Organization (auto-slug), Membership (4 roles, unique_together)
│   ├── views.py       — OrganizationViewSet, MembershipViewSet
│   ├── serializers.py — OrganizationSerializer (auto-owner on create), MembershipSerializer
│   ├── permissions.py — IsOrganizationMember, IsOrganizationAdmin
│   └── tests.py       — cross-org visibility, member vs admin, last owner protection (10 tests)
│
├── projects/        — Projects within organizations
│   ├── models.py      — Project (ACTIVE/ARCHIVED status)
│   ├── views.py       — ProjectViewSet (CRUD + summary + activity endpoints)
│   ├── serializers.py — ProjectSerializer (includes my_role for current user)
│   └── tests.py       — role-based create/update, outsider blocked, filter by status (8 tests)
│
└── tasks/           — Tasks within projects + ActivityLog
    ├── models.py      — Task (status, priority, assignee, due_date), ActivityLog (audit trail)
    ├── views.py       — TaskViewSet (CRUD + change-status), logs all mutations
    ├── serializers.py — TaskSerializer (validates assignee is org member), ActivityLogSerializer
    ├── urls.py        — Nested routes under projects/ and standalone tasks/
    ├── tests.py       — permissions, filters, pagination, activity log (22 tests)
```

## Config

```
config/
├── settings/
│   ├── base.py    — DRF, JWT, CORS, throttle, pagination, DB_PATH via env
│   ├── dev.py     — DEBUG=True
│   └── prod.py    — DEBUG=False
├── urls.py        — Route includes (auth, organizations, projects, tasks)
├── asgi.py
└── wsgi.py
```

## How to run

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Or with Docker (from project root): `make up`

API available at `http://localhost:8000/api/`.

Run tests: `python manage.py test` (46 tests) or `make test` (Docker).

## API endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | Register (email, password) |
| POST | `/api/auth/login/` | Login (returns JWT access + refresh) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| GET | `/api/auth/me/` | Current user profile |

### Organizations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/organizations/` | List user's organizations |
| POST | `/api/organizations/` | Create organization (creator becomes OWNER) |
| GET | `/api/organizations/{slug}/` | Retrieve organization |
| PUT | `/api/organizations/{slug}/` | Update organization (ADMIN+) |
| PATCH | `/api/organizations/{slug}/` | Partial update (ADMIN+) |
| DELETE | `/api/organizations/{slug}/` | Delete organization (OWNER) |

### Members (nested under org)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/organizations/{slug}/members/` | List members |
| POST | `/api/organizations/{slug}/members/` | Add member (ADMIN+) |
| PUT | `/api/organizations/{slug}/members/{id}/` | Update member role (ADMIN+) |
| PATCH | `/api/organizations/{slug}/members/{id}/` | Partial update role (ADMIN+) |
| DELETE | `/api/organizations/{slug}/members/{id}/` | Remove member (ADMIN+; last owner protected) |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/` | List projects (filter by `status`, `organization`) |
| GET | `/api/organizations/{slug}/projects/` | List projects within an org |
| POST | `/api/organizations/{slug}/projects/` | Create project (ADMIN+) |
| GET | `/api/projects/{id}/` | Retrieve project (includes `my_role`) |
| PUT/PATCH | `/api/projects/{id}/` | Update project (ADMIN+) |
| DELETE | `/api/projects/{id}/` | Delete project (ADMIN+) |
| GET | `/api/projects/{id}/summary/` | Task counts by status (TODO, IN_PROGRESS, DONE) |
| GET | `/api/projects/{id}/activity/` | Recent activity log entries |

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tasks/` | List tasks (filter by `status`, `priority`, `assignee`; search by `title`) |
| GET | `/api/projects/{project_id}/tasks/` | List tasks within a project |
| POST | `/api/projects/{project_id}/tasks/` | Create task (MEMBER+) |
| GET | `/api/tasks/{id}/` | Retrieve task |
| PUT/PATCH | `/api/tasks/{id}/` | Update task (creator or ADMIN+) |
| DELETE | `/api/tasks/{id}/` | Delete task (creator or ADMIN+) |
| PATCH | `/api/tasks/{id}/change-status/` | Change task status (assignee/creator or ADMIN+) |

## Permission model (3 layers)

1. **Queryset-level** (`get_queryset`): filters to only orgs/projects/tasks the user belongs to — cross-org data returns 404.
2. **View-level** (`permission_classes`): `IsAuthenticated` everywhere, `IsOrganizationAdmin` for member management.
3. **Object-level** (`perform_*`): role checks before create/update/destroy — e.g., VIEWER can't create tasks, only creator or ADMIN/OWNER can edit.

## Roles

| Role | Permissions |
|------|-------------|
| OWNER | Everything ADMIN can do, plus: cannot be demoted/removed (last owner protection) |
| ADMIN | Create/edit/delete projects, manage members, edit/delete any task |
| MEMBER | Create tasks, edit/delete own tasks, change status of own/assigned tasks |
| VIEWER | Read-only access to organization data |