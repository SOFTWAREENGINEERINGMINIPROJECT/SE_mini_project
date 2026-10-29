# Deviations from SRS / SAD / Test Plan

Things we did differently from the submitted documents (SRS v1.0, SAD v1.0, Test Plan v1.0) and why. SAD and Test Plan are updated to v1.1 where the change is just a design detail.

| # | Document / section | What the doc said | What we did | Why |
|---|---|---|---|---|
| 1 | SRS REQ-3, REQ-5 to REQ-7 | Admin adds / edits / deletes students, faculty, subjects and classes | Done through the Django admin site (`/admin`). Students can also be bulk added from Excel (REQ-4). No separate SAMS pages for this | Django admin already gives add / edit / delete with validation, so building the same pages again was not worth it in the time we had. Admin user needs staff access to open `/admin` |
| 2 | SAD 3.6 data model | `Subject` had a `faculty` field, separate `Enrollment` table | `Teaching` table (faculty, subject, class) and `ClassSection.students` instead | One subject can be taught to many classes by different faculty. Updated in SAD v1.1 |
| 3 | SAD 3.6 | - | Extra table `ShortageAlert` | Keeps a record of shortage mails so a student is mailed at most once a week per subject, not after every class |
| 4 | SAD 4.3 API | `/attendance/<id>/edit/`, `/leaves/<id>/approve/`, `/reports/generate/` | `/attendance/edit/`, `/leaves/<id>/decide/`, `/reports/class/`, `/reports/shortage/` | Editing works on a whole class + date + hour at once, approve and reject share one URL. Updated in SAD v1.1 |
| 5 | SRS REQ-19 | Approved leave days not counted as absent | On approve, only Absent records in the date range become Leave, Present stays Present. If attendance is marked later for an approved leave day, the student is saved as Leave | Same result for the percentage, and we don't overwrite days the student actually came |
| 6 | SRS 2.4, SAD 3.6 | MySQL 8.0 | MySQL for running the app, SQLite (`USE_SQLITE=1`) for local testing and GitHub Actions CI | CI doesn't need a MySQL server, tests run faster |
| 7 | Test Plan 5 | System testing with Selenium | System testing done manually in the browser. 73 automated Django tests run in GitHub Actions on every PR | Not enough time to set up Selenium |
| 8 | Test Plan 7 | Testing 12-10-2026 to 13-11-2026 | Testing done in the two sprints, 19-10 to 23-10 and 26-10 to 30-10-2026 | Sprint dates were given by the course after the Test Plan was submitted. Updated in Test Plan v1.1 |
| 9 | Mark attendance | - | Attendance cannot be marked for a future date | Added as a basic validation |

## Open items (not implemented)

These are requirements or design controls that are **not met**. Writing them here does not satisfy them, it only records the status so it is clear at the demo.

| Item | Source | Status | Reason | Risk | Owner | Decision |
|---|---|---|---|---|---|---|
| Performance limits (TC-15) | SRS NFR-1, NFR-2, NFR-3 | Not verified - test not run | No load testing tool set up in the sprint time | Response times under 100 users are unknown | Deepak | Team: run a basic timing test before the final demo if time permits, else deferred. To be confirmed with faculty at demo |
| Daily database backup | SRS NFR-4 | Not implemented - deferred | App only runs on our laptops, there is no server to schedule backups on. Manual backup possible: `mysqldump -u sams_user -p sams_db > backup.sql` | Data loss if a laptop database is lost | Gyaan | Team: deferred until the app is deployed on a server. To be confirmed with faculty at demo |
| Limit login attempts | SAD 3.9 (STRIDE, denial of service / spoofing) - security design control, not an SRS requirement | Not implemented - deferred | Not part of the SRS requirement list, left out for sprint time | Passwords can be brute forced | Santosh | Team: deferred. SAD 3.9 still lists it, so this is a gap against the design. To be confirmed with faculty at demo |
| PDF / Excel export | SRS REQ-14 | In progress (SEM-16) | - | Requirement not met until merged | Subhransi | Must be done before freeze (30-10-2026) |

