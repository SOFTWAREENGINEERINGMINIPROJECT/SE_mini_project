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
| SEM-5 | Login / logout | REQ-1 | 3 | Santosh | Done ([PR #19](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/19)) |
| SEM-6 | Role-based dashboard + `role_required` decorator | REQ-2, NFR-7 | 5 | Santosh | Done ([PR #19](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/19)) |
| SEM-9 | Admin: add subjects | REQ-5 | 2 | Deepak | Done ([PR #20](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/20)) |
| SEM-10 | Admin: add classes, assign faculty | REQ-6, REQ-7 | 3 | Deepak | Done ([PR #20](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/20)) |
| SEM-11 | Mark attendance | REQ-8, REQ-9 | 5 | Deepak | Done ([PR #20](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/20)) |
| SEM-14 | Student: my attendance | REQ-12, NFR-8 | 2 | Subhransi | Done ([PR #21](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/21)) |

Sprint 1 total: 30 points. Completed: 30.

## Sprint 2

| Key | Story | Covers | Points | Owner | Status |
|---|---|---|---|---|---|
| SEM-7 | Admin: add/edit/delete students & faculty | REQ-3, BR-1 | 5 | Santosh | Partly - done through Django admin (see docs/DEVIATIONS.md) |
| SEM-8 | Excel upload for students | REQ-4 | 8 | Santosh | Done ([PR #31](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/31)) |
| SEM-12 | Edit attendance within 3 days + audit log | REQ-10, NFR-11 | 5 | Deepak | Done ([PR #30](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/30)) |
| SEM-13 | `attendance_percent()` + shortage hook | REQ-11, BR-5 | 3 | Deepak | Done ([PR #29](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/29)) |
| SEM-15 | Report: class + subject + date range | REQ-13 | 5 | Subhransi | Done ([PR #25](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/25)) |
| SEM-16 | PDF / Excel report export | REQ-14 | 8 | Subhransi | In progress |
| SEM-17 | Shortage list (< 75%) | REQ-15, BR-4 | 3 | Subhransi | Done ([PR #33](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/33)) |
| SEM-20 | Shortage email | REQ-16 | 3 | Gyaan | Done ([PR #32](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/32)) |
| SEM-21 | Apply for leave | REQ-17 | 3 | Gyaan | Done ([PR #27](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/27)) |
| SEM-22 | Approve / reject leave | REQ-18, REQ-19 | 5 | Gyaan | Done ([PR #28](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/28)) |
| - | UI: role-based navigation links (#23) | REQ-2 | 2 | Subhransi | Done ([PR #24](https://github.com/SOFTWAREENGINEERINGMINIPROJECT/SE_mini_project/pull/24)) |

Sprint 2 total: 50 points (48 planned + 2 added).

## NFRs without a dedicated story

Covered as acceptance criteria on the stories above, or already satisfied by the Sprint 1 setup (SEM-18/19):

| NFR | Where it's satisfied |
|---|---|
| NFR-1, NFR-2, NFR-3 (performance) | Not measured yet (TC-15), see docs/DEVIATIONS.md |
| NFR-4 (daily DB backup) | Not automated, manual mysqldump, see docs/DEVIATIONS.md |
| NFR-5 (no hard delete) | Design constraint: attendance app never exposes a delete view |
| NFR-6 (hashed passwords) | Django default (PBKDF2), already true from SEM-18 |
| NFR-9 (30 min session timeout) | Set in `settings.py` (see HANDOFF.md) |
| NFR-10 (CSRF / SQL injection) | Django default (CSRF middleware, ORM) — don't use raw SQL |

## GitHub Project board

The org Projects board has a Sprint 1 and a Sprint 2 view. Issues carry the sprint, epic, owner and points labels.
