# Business Feedback

Business owners and managers can submit feedback (bugs, feature requests, complaints, general comments) about the BookNgon platform. Platform admins review and respond via the Django admin panel.

## Model

Located in `business/models.py` — `BusinessFeedback` inherits from `SoftDeleteModel`.

| Field | Type | Description |
|-------|------|-------------|
| `business` | FK → Business | The business submitting feedback |
| `submitted_by` | FK → Staff | The staff member who submitted |
| `category` | CharField | `bug`, `feature_request`, `general`, `complaint` |
| `subject` | CharField(255) | Short summary |
| `message` | TextField | Full feedback details |
| `status` | CharField | `pending`, `reviewed`, `in_progress`, `resolved`, `closed` |
| `admin_response` | TextField (nullable) | Platform admin's reply |
| `admin_responded_at` | DateTimeField (nullable) | When admin responded |

## API Endpoints

Base path: `/api/business-feedback/`

All endpoints require authentication and `IsBusinessManager` permission (Owner or Manager role).

### List feedbacks

```
GET /api/business-feedback/
```

Returns all feedbacks for the authenticated user's business.

### Create feedback

```
POST /api/business-feedback/
```

`business` and `submitted_by` are auto-set from the authenticated user.

**Request body:**

```json
{
  "category": "feature_request",
  "subject": "Add SMS reminders",
  "message": "It would be great to have automated SMS reminders for upcoming appointments."
}
```

**Response:**

```json
{
  "results": {
    "id": 1,
    "business": "uuid",
    "submitted_by": 1,
    "submitted_by_name": "John Doe",
    "category": "feature_request",
    "subject": "Add SMS reminders",
    "message": "It would be great to have automated SMS reminders for upcoming appointments.",
    "status": "pending",
    "admin_response": null,
    "admin_responded_at": null,
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T10:00:00Z"
  },
  "success": true,
  "status_code": 201
}
```

### Retrieve feedback

```
GET /api/business-feedback/{id}/
```

### Update feedback

```
PUT/PATCH /api/business-feedback/{id}/
```

Business users can update `category`, `subject`, and `message`. The fields `status`, `admin_response`, and `admin_responded_at` are read-only via the API.

### Delete feedback

```
DELETE /api/business-feedback/{id}/
```

## Admin Panel

Platform admins manage feedback at `/admin/business/businessfeedback/`.

- Feedback fields (`business`, `submitted_by`, `category`, `subject`, `message`) are **read-only** in admin
- Admins can update `status`, `admin_response`, and `admin_responded_at`

## Categories

| Value | Use case |
|-------|----------|
| `bug` | Something is broken or not working as expected |
| `feature_request` | Suggestion for a new feature or improvement |
| `general` | General comment or question |
| `complaint` | Dissatisfaction with the platform |

## Status Flow

```
pending → reviewed → in_progress → resolved
                                  → closed
```
