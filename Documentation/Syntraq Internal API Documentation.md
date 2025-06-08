# 🔌 Syntraq Internal API Documentation

## 🧭 Purpose
This API layer enables secure, structured communication between:
- Frontend (React/Tailwind)
- Backend (FastAPI)
- AI Agent Dispatcher
- Storage and File Handlers

---

## 🔐 Authentication & Headers

- Authentication: Bearer Token (JWT)
- Required Headers:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

---

## 🔍 1. Opportunities API

### `GET /api/opportunities`
Fetch all or filtered opportunities

**Query Params**:
- `status`: active | saved | archived
- `source`: sam | email | csv
- `fit_score_min`: int

### `POST /api/opportunities/upload`
Upload new opportunity (CSV, ZIP, PDF)

**Body**:
```json
{
  "source": "zip_upload",
  "file_url": "upload/attachments/rfp_bundle.zip"
}
