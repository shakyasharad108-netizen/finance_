# Finance Dashboard API

A production-ready REST API for personal finance tracking, built with **Django + Django REST Framework**.  
Implements clean architecture, JWT authentication, and role-based access control.

---

## Quick Start

```bash
# 1. Clone and set up environment
git clone <repo>
cd finance_dashboard
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY

# 4. Run migrations
python manage.py migrate

# 5. Create an admin user
python manage.py createsuperuser

# 6. Start the server
python manage.py runserver
```

**Interactive API docs** available at: `http://localhost:8000/api/docs/`  
**Django Admin** at: `http://localhost:8000/admin/`

---

## Architecture Overview

```
finance_dashboard/
├── config/                  # Django project config
│   ├── settings.py          # All settings, clearly sectioned
│   └── urls.py              # Root URL router (versioned /api/v1/)
│
├── apps/
│   ├── core/                # Shared infrastructure
│   │   ├── models.py        # BaseModel (UUID PK, timestamps, soft delete)
│   │   ├── exceptions.py    # Custom exception handler + ServiceError
│   │   ├── permissions.py   # RBAC permission classes
│   │   ├── pagination.py    # Consistent paginated response shape
│   │   └── responses.py     # success_response / error_response helpers
│   │
│   ├── users/               # Authentication & user management
│   │   ├── models.py        # Custom User model with role field
│   │   ├── serializers.py   # Register, Update, ChangeRole serializers
│   │   ├── services.py      # UserService — all user business logic
│   │   ├── views.py         # Thin views, delegate to services
│   │   ├── admin.py         # Django admin registration
│   │   └── urls/
│   │       ├── auth_urls.py  # /api/v1/auth/*
│   │       └── user_urls.py  # /api/v1/users/*
│   │
│   └── finance/             # Core finance feature
│       ├── models.py        # Category + FinancialRecord models
│       ├── serializers.py   # Record, Category, Dashboard serializers
│       ├── services.py      # RecordService, CategoryService, DashboardService
│       ├── filters.py       # django-filter FilterSet for records
│       ├── views.py         # Thin views, delegate to services
│       ├── admin.py         # Django admin
│       └── urls.py          # /api/v1/finance/*
│
├── requirements.txt
├── .env.example
├── API_DOCS.md              # Full API reference with sample JSON
└── README.md
```

### Layered Architecture

```
Request
  ↓
View          — parse request, call serializer, return response
  ↓
Serializer    — validate & deserialize input, serialize output
  ↓
Service       — business logic, data access, raise ServiceError on violations
  ↓
Model/ORM     — database queries
```

**Why this matters:**
- **Views** contain zero business logic — they're purely HTTP adapters.
- **Services** are plain Python classes — testable without an HTTP client.
- **Serializers** handle all input validation; services trust validated data.
- **Models** stay thin — data structure + soft delete, nothing more.

---

## Role-Based Access Control

| Operation                        | Viewer | Analyst | Admin |
|----------------------------------|:------:|:-------:|:-----:|
| Read own financial records       |   ✓    |    ✓    |   ✓   |
| Read all financial records       |        |         |   ✓   |
| Create financial records         |        |    ✓    |   ✓   |
| Update own financial records     |        |    ✓    |   ✓   |
| Update any financial record      |        |         |   ✓   |
| Delete financial records         |        |         |   ✓   |
| Access dashboard analytics       |        |    ✓    |   ✓   |
| Manage categories (own)          |   ✓    |    ✓    |   ✓   |
| List all users                   |        |         |   ✓   |
| Change user roles                |        |         |   ✓   |
| Deactivate users                 |        |         |   ✓   |

**Role enforcement happens in two places:**
1. `core/permissions.py` — DRF permission classes on views (coarse-grained)
2. `services.py` — method-level checks (fine-grained, e.g. "analyst can only edit own records")

---

## Key Design Decisions

### 1. Custom User Model from Day 1
Django's docs recommend defining a custom user model at project start.  
Adding `role` here avoids a separate `Profile` model for a simple, fixed set of roles.

### 2. UUID Primary Keys
All models use UUID PKs. This prevents enumeration attacks (`/records/1`, `/records/2`)
and is friendly for distributed systems.

### 3. Soft Delete
Records are never removed from the database — `is_deleted=True` hides them via
the default `SoftDeleteManager`. Admins can audit all records. The `all_objects`
manager bypasses the soft-delete filter for admin/recovery use cases.

### 4. Service Layer
Business logic never lives in views or serializers. Services are:
- Independently testable (no request/response objects)
- Reusable (management commands, Celery tasks, admin actions)
- Easy to audit — "where does X happen?" → look in services.py

### 5. Consistent Response Envelope
Every endpoint returns `{ error, message, data }` or `{ error, message, errors }`.
The custom exception handler in `core/exceptions.py` converts DRF's variable
error formats into this consistent shape automatically.

### 6. JWT with Refresh Token Rotation
`ROTATE_REFRESH_TOKENS = True` + `BLACKLIST_AFTER_ROTATION = True` means
refresh tokens are single-use. This limits the blast radius of a leaked token.

### 7. Data Scoping by Role
Admin users see all records. Analysts and Viewers see only their own.
This scoping is centralized in `RecordService._base_queryset()` and
`DashboardService._get_scoped_qs()` — not scattered across views.

---

## Environment Variables

| Variable       | Default              | Description                  |
|----------------|----------------------|------------------------------|
| `SECRET_KEY`   | (required)           | Django secret key            |
| `DEBUG`        | `True`               | Debug mode                   |
| `ALLOWED_HOSTS`| `*`                  | Comma-separated allowed hosts|
| `DB_ENGINE`    | `mysql`            | Database backend             |
| `DB_NAME`      | `db.mysql`         | Database name / path         |
| `DB_USER`      | (blank)              | Database user                |
| `DB_PASSWORD`  | (blank)              | Database password            |
| `DB_HOST`      | (blank)              | Database host                |
| `DB_PORT`      | (blank)              | Database port                |

---

## Running Tests

```bash
python manage.py test apps
```

Test structure mirrors the app structure:
```
apps/
  users/tests/
    test_models.py
    test_services.py
    test_views.py
  finance/tests/
    test_models.py
    test_services.py
    test_views.py
```

---

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Set a strong random `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Switch `DB_ENGINE` to PostgreSQL
- [ ] Set `CORS_ALLOWED_ORIGINS` (remove `CORS_ALLOW_ALL_ORIGINS`)
- [ ] Configure a reverse proxy (nginx/caddy) in front of gunicorn
- [ ] Run `python manage.py collectstatic`
- [ ] Set up log aggregation

---

## Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Framework     | Django 4.2 + DRF 3.14               |
| Auth          | djangorestframework-simplejwt 5.3   |
| Filtering     | django-filter 23.5                  |
| API Docs      | drf-spectacular (OpenAPI 3.0)       |
| CORS          | django-cors-headers                 |
| Config        | python-decouple                     |
| Database      | SQLite (dev) / PostgreSQL (prod)    |


## Live API
https://finance-9v6v.onrender.com/api/docs/

## Base URL
https://finance-9v6v.onrender.com/

## Example Endpoints
- POST /api/v1/auth/login/
- GET /api/v1/finance/
- GET /api/v1/users/
