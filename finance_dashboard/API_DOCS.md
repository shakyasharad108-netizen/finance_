# Finance Dashboard — API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints (except Register and Login) require:
```
Authorization: Bearer <access_token>
```

All responses follow the envelope:
```json
{ "error": false, "message": "...", "data": ... }
```
Errors:
```json
{ "error": true, "message": "...", "errors": { ... } }
```

---

## Authentication

### POST `/auth/register/`
**Access:** Public

**Request:**
```json
{
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith",
  "password": "securepass123",
  "confirm_password": "securepass123"
}
```

**Response `201`:**
```json
{
  "error": false,
  "message": "Account created successfully.",
  "data": {
    "id": "3f9a1c2d-...",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "full_name": "Alice Smith",
    "role": "viewer",
    "is_active": true,
    "date_joined": "2025-01-15T10:00:00Z"
  }
}
```

---

### POST `/auth/login/`
**Access:** Public

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "securepass123"
}
```

**Response `200`:**
```json
{
  "error": false,
  "message": "Login successful.",
  "data": {
    "access": "eyJhbGci...",
    "refresh": "eyJhbGci...",
    "user": {
      "id": "3f9a1c2d-...",
      "email": "alice@example.com",
      "role": "viewer"
    }
  }
}
```

---

### POST `/auth/logout/`
**Access:** Any authenticated user

**Request:**
```json
{ "refresh": "eyJhbGci..." }
```

**Response `200`:**
```json
{ "error": false, "message": "Logged out successfully.", "data": null }
```

---

### POST `/auth/token/refresh/`
**Access:** Public (with valid refresh token)

**Request:**
```json
{ "refresh": "eyJhbGci..." }
```

**Response `200`:**
```json
{ "access": "eyJhbGci...", "refresh": "eyJhbGci..." }
```

---

### GET `/auth/me/`
**Access:** Any authenticated user

**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": {
    "id": "3f9a1c2d-...",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "role": "viewer"
  }
}
```

---

### PATCH `/auth/me/`
**Access:** Any authenticated user (updates own profile)

**Request:**
```json
{ "first_name": "Alicia" }
```

---

### POST `/auth/change-password/`
**Request:**
```json
{
  "old_password": "securepass123",
  "new_password": "newpass456",
  "confirm_new_password": "newpass456"
}
```

---

## User Management (Admin only)

### GET `/users/`
Returns all active users.

**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": [
    { "id": "...", "email": "alice@example.com", "role": "viewer" },
    { "id": "...", "email": "bob@example.com",   "role": "analyst" }
  ]
}
```

---

### GET `/users/<id>/`
### PATCH `/users/<id>/`

**PATCH Request:**
```json
{ "first_name": "Robert" }
```

---

### DELETE `/users/<id>/`
Deactivates the user (not deleted from DB).

**Response `200`:**
```json
{ "error": false, "message": "User deactivated.", "data": null }
```

---

### PATCH `/users/<id>/role/`

**Request:**
```json
{ "role": "analyst" }
```

**Response `200`:**
```json
{
  "error": false,
  "message": "Role updated.",
  "data": { "id": "...", "email": "alice@example.com", "role": "analyst" }
}
```

---

## Financial Records

### GET `/finance/records/`
**Access:** All roles (Viewers see own; Admins see all)

**Query Params:**
| Param           | Type   | Example        | Description              |
|-----------------|--------|----------------|--------------------------|
| `transaction_type` | string | `income`    | Filter by type           |
| `category`      | UUID   | `abc123-...`   | Filter by category       |
| `date_from`     | date   | `2025-01-01`   | Start date (inclusive)   |
| `date_to`       | date   | `2025-01-31`   | End date (inclusive)     |
| `min_amount`    | number | `100`          | Minimum amount           |
| `max_amount`    | number | `5000`         | Maximum amount           |
| `search`        | string | `salary`       | Search title             |
| `ordering`      | string | `-date`        | Sort field               |
| `page`          | int    | `2`            | Page number              |
| `page_size`     | int    | `10`           | Results per page (max 100)|

**Response `200`:**
```json
{
  "error": false,
  "count": 42,
  "next": "http://localhost:8000/api/v1/finance/records/?page=2",
  "previous": null,
  "results": [
    {
      "id": "7a3b...",
      "title": "Freelance Payment",
      "transaction_type": "income",
      "amount": "2500.00",
      "date": "2025-01-14",
      "category_name": "Freelance",
      "created_at": "2025-01-14T09:30:00Z"
    }
  ]
}
```

---

### POST `/finance/records/`
**Access:** Analyst, Admin

**Request:**
```json
{
  "title": "Grocery shopping",
  "transaction_type": "expense",
  "amount": "85.50",
  "date": "2025-01-15",
  "category": "c1d2e3f4-...",
  "notes": "Weekly groceries at Whole Foods"
}
```

**Response `201`:**
```json
{
  "error": false,
  "message": "Financial record created.",
  "data": {
    "id": "9b8c...",
    "title": "Grocery shopping",
    "transaction_type": "expense",
    "amount": "85.50",
    "date": "2025-01-15",
    "category": "c1d2e3f4-...",
    "category_name": "Groceries",
    "notes": "Weekly groceries at Whole Foods",
    "created_at": "2025-01-15T11:00:00Z",
    "updated_at": "2025-01-15T11:00:00Z"
  }
}
```

**Validation Errors `400`:**
```json
{
  "error": true,
  "message": "amount: Amount must be greater than zero.",
  "errors": {
    "amount": ["Amount must be greater than zero."]
  }
}
```

---

### GET `/finance/records/<id>/`
### PATCH `/finance/records/<id>/`

**PATCH Request (partial update):**
```json
{ "notes": "Updated note", "amount": "90.00" }
```

---

### DELETE `/finance/records/<id>/`
**Access:** Admin only  
Soft-deletes the record (sets `is_deleted=true`, preserved in DB).

---

## Categories

### GET `/finance/categories/`
**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": [
    { "id": "c1d2...", "name": "Groceries", "description": "", "created_at": "..." },
    { "id": "e5f6...", "name": "Salary",    "description": "Monthly salary", "created_at": "..." }
  ]
}
```

### POST `/finance/categories/`
```json
{ "name": "Utilities", "description": "Electricity, water, internet" }
```

### PATCH `/finance/categories/<id>/`
### DELETE `/finance/categories/<id>/`  (soft delete)

---

## Dashboard & Analytics
**Access:** Analyst, Admin only (Viewers receive 403)

### GET `/finance/dashboard/summary/`
**Query Params:** `date_from`, `date_to`

**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": {
    "total_income":  "12500.00",
    "total_expense":  "4320.75",
    "net_balance":    "8179.25",
    "record_count":   47
  }
}
```

---

### GET `/finance/dashboard/categories/`
**Query Params:** `date_from`, `date_to`

**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": [
    { "category_id": "c1d2...", "category_name": "Salary",    "transaction_type": "income",  "total": "10000.00", "count": 2 },
    { "category_id": "e5f6...", "category_name": "Groceries", "transaction_type": "expense", "total": "640.50",   "count": 8 },
    { "category_id": null,      "category_name": "Uncategorised", "transaction_type": "expense", "total": "199.00", "count": 3 }
  ]
}
```

---

### GET `/finance/dashboard/recent/`
**Query Params:** `limit` (default 10, max 50)

**Response `200`:**
```json
{
  "error": false,
  "message": "Success",
  "data": [
    { "id": "...", "title": "Netflix",  "transaction_type": "expense", "amount": "15.99", "date": "2025-01-15", "category_name": "Subscriptions" },
    { "id": "...", "title": "Freelance","transaction_type": "income",  "amount": "500.00","date": "2025-01-14", "category_name": "Freelance" }
  ]
}
```

---

## Error Reference

| HTTP Status | When                                        |
|-------------|---------------------------------------------|
| 400         | Validation error, bad input                 |
| 401         | Missing or invalid JWT token                |
| 403         | Authenticated but role lacks permission     |
| 404         | Resource not found                          |
| 405         | Method not allowed on endpoint              |
