
# 📐 Syntraq Technical Architecture (Markdown Representation)

```
Syntraq AI Platform - Technical Architecture

1. User Interface (Frontend) - React + Tailwind
   ├── /opportunities               → Unified Opportunity Feed (UOF)
   ├── /opportunities/saved        → Saved Opportunities View
   ├── /proposal-workspace         → Proposal Management Engine (PME)
   ├── /team-simulation            → ARTS (AI Role-Based Team Simulation)
   ├── /post-award                 → Post-Award Readiness Suite (PARS)
   ├── /settings / /profile        → Company Profile, Preferences
   └── UI Features:
       ├── Smart Filters, Dashboards, Timeline Views
       └── Export Tools (CSV, PDF, Google Docs)

2. Backend Server - FastAPI
   ├── /api/opportunities          → Ingest, parse, de-duplicate data
   ├── /api/analyze                → AI summary, Fit Score, compliance checks
   ├── /api/proposals              → Save, edit, lock proposals
   ├── /api/agents                 → Dispatch AI agents (Writer, Reviewer, etc.)
   ├── /api/files                  → Handle uploads (PDF, DOCX, XLSX, ZIP, etc.)
   ├── /api/forms                  → Auto-fill SF forms, attachments
   ├── /api/notifications          → Slack/email alerts, reminders
   └── Middleware:
       ├── Auth, Role-based Access
       └── Logging, Error Handling

3. AI Engine Layer - OpenAI (temporary) → Local LLM (future)
   ├── Summarizer AI               → Generates 30-sec briefs
   ├── Writer AI                   → Proposal narratives
   ├── Compliance AI               → FAR/DFARS mapping, section validation
   ├── Research AI                 → Pulls competitor & teaming intel
   ├── Pricing AI                  → Cost realism & margin simulation
   ├── Reviewer AI                 → Quality scoring and edits
   └── Scheduler AI                → Timeline prediction, progress balancing

4. Data Sources
   ├── SAM.gov API (mock/live)     → Solicitations, notices
   ├── FPDS API / USAspending      → Award history
   ├── GSA Advantage / SBA DSBS    → Pricing, teaming info
   ├── Email Ingestion (GovDelivery) → Digest parsing
   ├── Google Sheets Sync          → Manual watchlists
   └── OCR Engine (Tesseract)      → ZIP/PDF scans, embedded files

5. Storage
   ├── Local JSON / SQLite (dev)   → Proposals, metadata
   ├── Google Drive Integration    → Optional cloud sync
   ├── File Storage (Local/Cloud)  → Uploads, templates, attachments
   └── Version Control Layer       → Proposal versions, edit history

6. Post-Award Layer (PARS)
   ├── Contract Kickoff Planner
   ├── Compliance Tracker
   ├── Task & Delivery Scheduler
   ├── Invoice & Form Generator
   └── Performance Dashboard

7. Admin + Ops
   ├── User Management
   ├── Role Permissions
   ├── API Keys / Env Config
   └── Logs, Backups, Uptime Monitor
```

---

## 🧩 Architecture Highlights
- **Modular, Service-Oriented** structure with separate layers for UI, API, AI, and storage
- **LLM-ready**, with fallback to local models for production privacy and performance
- **Pluggable sources**, allowing both live API and manual uploads
- **AI agents** are role-driven, not just task-specific (enabling autonomous orchestration)
- **Tightly integrated** pre-award → proposal → post-award continuity
