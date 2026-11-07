# Smart Roster Management System – DataStraw

A full-stack workforce scheduling application for a multi-brand customer experience operation. It models employees, brands, processes, pods, operating calendars, leave, public holidays, resource allocations and monthly roster entries. The scheduling service uses deterministic constraint-first assignment and persists uncovered staffing requirements as critical conflicts.

## Problem statement

Operations teams need to staff brand/process work across different calendars while respecting individual weekly offs, approved leave and availability. A single person's absence can create a client coverage gap; a shared-resource brand may be able to absorb an absence. This system makes those relationships explicit, generates monthly assignments and surfaces unresolved coverage gaps for manager review.

## Features

- Employee, brand, process and pod records stored in SQLite through SQLAlchemy.
- Many-to-many employee/brand and employee/process relationships.
- Per-brand/process operating calendars: `ALL_DAYS`, `NO_PUBLIC_HOLIDAYS`, `SUNDAYS_AND_HOLIDAYS_OFF`, plus explicit weekdays.
- Per-rule minimum staffing and shift windows.
- Approved leave, pending leave, approved comp-off, employee weekly offs and public holidays.
- Month/year roster generation and company, pod, brand, process and employee filtering (the roster API supports all those dimensions).
- Critical coverage-gap records with date, brand, process and staffing explanation.
- Backup candidate endpoint for a manager to review before reassignment.
- Manual assignment endpoint, roster removal endpoint and revalidation endpoint.
- Dashboard metrics, pod distribution, brand resource model and workload analytics.
- React/Vite interface with responsive navigation, tables, filters, charts and add-record forms.

## Technology

- Frontend: React, Vite, Tailwind CSS, Recharts, Lucide React.
- Backend: Python, Flask, Flask-CORS.
- Persistence: SQLite, Flask-SQLAlchemy / SQLAlchemy ORM.
- Tests: pytest.

## Architecture

```text
React + Vite UI (5173)
        | JSON / REST
        v
Flask API (5000) ---- scheduler.py (deterministic assignment + validation)
        |
        v
SQLAlchemy ORM
        |
        v
SQLite (smart_roster.db)
```

### Database model

| Table | Purpose |
|---|---|
| employees | Employee identity, pod, availability and weekly-off preference |
| brands | Client accounts |
| processes | CS, ACC, Retention, NDR and configurable additional processes |
| pods | Operational pods and pod lead |
| employee_brands | Many-to-many employee/brand resource allocation |
| employee_processes | Many-to-many employee/process skill allocation |
| operating_rules | Brand + process calendar, minimum staffing and shift window |
| leave_requests | Planned leave and approval state |
| comp_offs | Approved employee comp-off dates |
| public_holidays | Organisation holiday calendar |
| roster_entries | Dated employee/brand/process assignments and shift |
| conflicts | Persisted critical coverage gaps |
| generation_history | Month generation counts and timestamp |

Foreign keys and uniqueness constraints protect core relationships. SQLite is used for local setup; the ORM schema is portable to PostgreSQL by changing `SQLALCHEMY_DATABASE_URI` to a PostgreSQL connection string and installing a PostgreSQL DB driver.

## Scheduling algorithm

1. Remove previously generated entries and unresolved conflicts for the selected month.
2. For each calendar day and each configured brand/process operating rule, determine whether that rule operates using its calendar and weekday mask.
3. Find active employees allocated to both that brand and process.
4. Exclude employees with unavailable status, matching weekly off, approved leave, approved comp-off, or a shift overlapping an existing assignment that day.
5. Sort eligible employees deterministically by accumulated monthly workload, preferred-off penalty and employee ID.
6. Select up to `min_staff` eligible employees and persist their shift assignments.
7. If the selected count is below the required minimum, persist a `CRITICAL / COVERAGE_GAP` conflict with the date, brand, process, required count and actual count.

Mandatory availability, calendar, leave and shift-overlap rules are treated as hard constraints. Preferred weekly offs are a soft preference and do not override required coverage. The current implementation is a deterministic greedy scheduler, not a global mathematical optimiser; it is intentionally transparent and reproducible. It does not silently mark a month as valid when coverage is missing.

## Sample data and assumptions

`backend/seed.py` creates 30 fictional employees, 15 brands, 5 processes and 4 pods. Twelve of fifteen brands (80%) have one dedicated employee; the remaining three brands each have six allocated employees to make a 30-person sample feasible while preserving shared-resource behaviour. The multi-resource brands have process-specific assignments and intentional overlapping CS skills. The sample includes multiple weekly-off patterns, three November 2026 public holidays, approved and pending planned leave, an approved comp-off, different brand calendars and minimum staffing of two for selected shared-brand CS rules.

The seed uses November 2026 dates to make the change-management demo repeatable. Employees are not assigned shifts on their individual weekly-off day even if the client process operates that day. A client calendar and an employee schedule are separate concepts.

## Setup – Windows

Prerequisites: Python 3.10+ and Node.js 20+.

### 1. Backend

Open PowerShell in the project folder:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python run.py
```

The API runs at `http://localhost:5000`. Health check: `http://localhost:5000/api/health`.

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current terminal, then activate again. Alternatively run `.venv\Scripts\python.exe` directly.

### 2. Frontend

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend defaults to `http://localhost:5000/api`. To point it elsewhere, create `frontend/.env` with `VITE_API_URL=https://your-api-host/api` and restart Vite.

### 3. Regenerate sample data

Stop the backend, then run `python seed.py` from `backend`. This resets the local database and reseeds the demo data.

## API reference

All routes are prefixed with `/api`. JSON request/response bodies are used.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health |
| GET | `/dashboard` | Dashboard counts and coverage metrics |
| GET/POST | `/employees` | List/create employees |
| PUT/DELETE | `/employees/{id}` | Update/deactivate employee |
| GET/POST | `/brands` | List/create brands |
| PUT/DELETE | `/brands/{id}` | Update/deactivate brand |
| GET/POST | `/processes` | List/create processes |
| PUT | `/processes/{id}` | Update process |
| GET/POST | `/pods` | List/create pods |
| GET/POST | `/rules` | List/create operating rules |
| PUT | `/rules/{id}` | Update operating rule |
| GET/POST | `/leaves` | List/create leave requests |
| PUT | `/leaves/{id}` | Approve/update leave status |
| GET/POST | `/holidays` | List/create public holidays |
| POST | `/roster/generate` | Generate a month: `{ "month": 11, "year": 2026 }` |
| GET | `/roster?month=11&year=2026` | List roster entries; optional `pod_id`, `brand_id`, `process_id`, `employee_id` filters |
| POST | `/roster/recommend` | Find eligible backup candidates for a date and brand/process |
| POST | `/roster/manual` | Add a manager-created assignment |
| DELETE | `/roster/{id}` | Remove an assignment |
| POST | `/roster/revalidate` | Regenerate and revalidate selected month |
| GET | `/conflicts` | List unresolved conflicts |

## Tests

From `backend`:

```powershell
pip install -r requirements.txt
pytest -q
```

Tests cover API health and CRUD basics, database-backed test setup, monthly generation, Sunday-off handling, calendar holiday behaviour, approved leave exclusion and single-resource coverage failure. Run tests after changing scheduler rules.

## Change-management demonstration

1. Generate November 2026.
2. Open Conflict Center and use **Simulate employee unavailability** to add an approved one-day leave to the first seeded employee.
3. Revalidate the selected month. Since the first twelve brands are single-resource, that employee's brand/process coverage should surface as a critical gap on the affected operating day.
4. Review backup candidates with `POST /api/roster/recommend` using the affected brand, process, date and employee ID. The endpoint returns only eligible employees already allocated to the same brand and process.
5. A manager can add a chosen backup with `POST /api/roster/manual`, then run `/api/roster/revalidate` to confirm coverage.
6. For a multi-resource brand, an unavailable employee is excluded and the other eligible resources can meet the minimum staffing requirement if sufficient resources remain.

## Section 8 – Tell us how you think

**1. How did you model employees, brands, processes, pods, and their relationships?**  
Employees belong to one operational pod and have many-to-many relationships with brands and processes. Brands and processes are connected through operating-rule records, because a brand can operate several processes and each process can have different calendar and staffing requirements. Pod lead is represented on the pod record.

**2. How does your system generate a roster and determine whether it satisfies the required constraints?**  
The scheduler iterates through each day and each active brand/process rule, calculates eligible employees after applying availability, weekly-off, leave, comp-off, holiday and shift-overlap constraints, then selects the lowest-workload eligible resources up to the minimum staffing count. If the count is insufficient, a critical conflict is persisted with the exact date and requirement.

**3. How did you handle the difference between single-resource brands and brands with multiple employees?**  
The same relational allocation model supports either one or multiple employees per brand. A single-resource brand has one employee in its resource relationship; a shared brand has several, potentially with different process skills and overlapping skills. Minimum staffing is configured per brand/process rule rather than hard-coded by brand type.

**4. What happens when an employee manages all processes for a brand but is unavailable on a required working day?**  
That employee is excluded from the eligible pool for the date. The generator records a coverage gap for each operating process whose minimum staffing cannot be met. The manager can inspect eligible backups and approve an additional allocation or reassignment, then revalidate.

**5. How does your system handle conflicting requirements or insufficient staffing?**  
Mandatory constraints (operating day, active status, availability, leave, weekly off, comp-off and shift overlap) filter out invalid candidates. If fewer than the required minimum remain, the system stores a critical coverage conflict instead of silently treating the roster as complete. Preferences only influence selection order.

**6. Which parts of the process did you automate, and which did you leave under human control? Why?**  
Calendar evaluation, candidate filtering, workload-aware selection, roster persistence and gap detection are automated. A manager retains control over approving leave, selecting backup resources, changing operating requirements and deciding whether a roster is ready to publish. Those decisions can affect client commitments and should be reviewable.

**7. If the company doubled its team and brand count, what would you change about your solution?**  
I would move production persistence to PostgreSQL, introduce schema migrations, add indexes for date/resource lookups, separate scheduling into a background job queue, and use a constraint solver such as OR-Tools if cross-month fairness or complex shift rules make greedy scheduling insufficient. I would also add role-based access, audit logs, pagination and deployment observability.

**8. If you had one additional week to work on this, what would you improve first?**  
I would implement a full edit-and-approve workflow with audit history, make backup recommendations include cross-trained employees who can be formally allocated, add a global optimisation pass for fair weekly-off distribution, and expand integration tests for multi-brand double-booking and manual-change revalidation. I would also complete production authentication and role-based permissions.

## Known limitations / honest scope

- This is an assessment/demo application, not a hardened production HR platform. Authentication, authorisation, audit logging, email notifications and deployment secrets management are not implemented.
- The scheduling strategy is deterministic greedy selection, not OR-Tools/global optimisation. It can report a conflict in a case where a more advanced solver might find a better global arrangement.
- The manager-created manual assignment endpoint persists an assignment; the manager should call revalidation afterwards. A complete edit-in-place UI and publish/approval workflow remain future work.
- The current frontend has create forms and list views; some advanced editing/deactivation actions are exposed through the REST API rather than all being surfaced in the UI.
- Public holiday calendar configuration is organisation-wide in this version; region- or employee-specific holiday calendars can be added to the schema.
- Dashboard coverage is a high-level assignment-to-rule indicator, not a substitute for inspecting dated conflict records.

## Deployment

Deploy the Flask backend and React static frontend as separate services. Configure a persistent PostgreSQL database for production and set `SQLALCHEMY_DATABASE_URI` in the backend environment. Install backend requirements, run the seed script once for demo data, and start Flask behind a production WSGI server (for example Gunicorn). Build the frontend with `npm run build` and publish `frontend/dist`; set `VITE_API_URL` at build time to the deployed API URL. Configure CORS to allow only the deployed frontend origin before public release. Do not use Flask's development server in production.

## Submission checklist

- [x] Source code, README, requirements and package manifest
- [x] SQLAlchemy schema and SQLite seed script
- [x] REST endpoints for core data and roster operations
- [x] Deterministic scheduling and persisted coverage conflicts
- [x] React dashboard, roster views, tables and analytics
- [x] Section 8 answers
- [ ] Public application URL (requires deployment credentials/account)
- [ ] GitHub repository URL (requires user-owned GitHub access)
- [ ] Recorded 3–5 minute demo video (script can be prepared; recording requires user action)
- [ ] LinkedIn profile URL (must be supplied by applicant)
