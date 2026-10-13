# Backlog — SAMS

Mirrors the [GitHub Issues](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/issues) (source of truth — issue state is what's current). Every item below traces to an FR/NFR in `docs/SRS_Team1_SAMS.pdf` §5/§6. Jira keys match the team's internal Jira (per HANDOFF.md) so a Jira key and a GitHub issue always refer to the same story.

**Sprints:** Sprint 1 = 19–23 Oct 2026 · Sprint 2 = 26–30 Oct 2026 (dry-run/backlog week: 12–16 Oct).

## Epics

| Epic | Owner |
|---|---|
| SEM-1 — accounts | Santosh |
| SEM-2 — academics + attendance | Deepak |
| SEM-3 — reports | Subhransi |
| SEM-4 — leaves | Gyaan |

## Sprint 1

| Key | Story | Covers | Points | Owner | Status |
|---|---|---|---|---|---|
| SEM-18 | Django project setup | SRS 2.5 | 5 | Gyaan | Done |
| SEM-19 | Shared models for all apps | backbone for REQ-1..19 | 5 | Gyaan | Done |
| SEM-5 | Login / logout | REQ-1 | 3 | Santosh | In review ([PR #19](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/19)) |
| SEM-6 | Role-based dashboard + `role_required` decorator | REQ-2, NFR-7 | 5 | Santosh | In review ([PR #19](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/19)) |
| SEM-9 | Admin: add subjects | REQ-5 | 2 | Deepak | To do |
| SEM-10 | Admin: add classes, assign faculty | REQ-6, REQ-7 | 3 | Deepak | To do |
| SEM-11 | Mark attendance | REQ-8, REQ-9 | 5 | Deepak | To do |
| SEM-14 | Student: my attendance | REQ-12, NFR-8 | 2 | Subhransi | To do |

Sprint 1 total: 30 points.

## Sprint 2

| Key | Story | Covers | Points | Owner |
|---|---|---|---|---|
| SEM-7 | Admin: add/edit/delete students & faculty | REQ-3, BR-1 | 5 | Santosh |
| SEM-8 | Excel upload for students | REQ-4 | 8 | Santosh |
| SEM-12 | Edit attendance within 3 days + audit log | REQ-10, NFR-11 | 5 | Deepak |
| SEM-13 | `attendance_percent()` + shortage hook | REQ-11, BR-5 | 3 | Deepak |
| SEM-15 | Report: class + subject + date range | REQ-13 | 5 | Subhransi |
| SEM-16 | PDF / Excel report export | REQ-14 | 8 | Subhransi |
| SEM-17 | Shortage list (< 75%) | REQ-15, BR-4 | 3 | Subhransi |
| SEM-20 | Shortage email | REQ-16 | 3 | Gyaan |
| SEM-21 | Apply for leave | REQ-17 | 3 | Gyaan |
| SEM-22 | Approve / reject leave | REQ-18, REQ-19 | 5 | Gyaan |

Sprint 2 total: 48 points.

## NFRs without a dedicated story

Covered as acceptance criteria on the stories above, or already satisfied by the Sprint 1 setup (SEM-18/19):

| NFR | Where it's satisfied |
|---|---|
| NFR-1, NFR-2, NFR-3 (performance) | Verified at demo against the Test Plan, not a separate story |
| NFR-4 (daily DB backup) | Ops task, not app code — do before Sprint 2 freeze |
| NFR-5 (no hard delete) | Design constraint: attendance app never exposes a delete view |
| NFR-6 (hashed passwords) | Django default (PBKDF2), already true from SEM-18 |
| NFR-9 (30 min session timeout) | Set in `settings.py` (see HANDOFF.md) |
| NFR-10 (CSRF / SQL injection) | Django default (CSRF middleware, ORM) — don't use raw SQL |

## GitHub Project board

A GitHub Projects (v2) board gives the same backlog a Kanban/Table view linked to this repo. Creating one needs repo-admin project access the current token doesn't carry, so it's a 90-second manual step for whoever has admin on the repo:

1. Repo → **Projects** tab → **New project** → **Board**.
2. **Add items** → filter by repo `SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project` → add all open issues.
3. Group by the `sprint-1` / `sprint-2` labels (or add a custom "Sprint" field).

Everything the board would show — points, owner, sprint, epic — is already on each issue as labels, so the board is a view, not new data.
