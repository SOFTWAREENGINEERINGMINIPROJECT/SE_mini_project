# Deviations from SRS / SAD / Test Plan

Things we did differently from the submitted documents (SRS v1.0, SAD v1.0, Test Plan v1.0) and why. SAD and Test Plan are updated to v1.1 where the change is just a design detail.

| # | Document / section | What the doc said | What we did | Why |
|---|---|---|---|---|
| 1 | SRS REQ-3, REQ-5 to REQ-7 | Admin adds / edits / deletes students, faculty, subjects and classes | Done through the Django admin site (`/admin`). Students can also be bulk added from Excel (REQ-4). No separate SAMS pages for this | Django admin already gives add / edit / delete with validation, so building the same pages again was not worth it in the time we had. Admin user needs staff access to open `/admin` |
| 2 | SAD 3.6 data model | `Subject` had a `faculty` field, separate `Enrollment` table | `Teaching` table (faculty, subject, class) and `ClassSection.students` instead | One subject can be taught to many classes by different faculty. Updated in SAD v1.1 |
| 3 | SAD 3.6 | - | Extra table `ShortageAlert` | Keeps a record of shortage mails so a student is mailed at most once a week per subject, not after every class |
| 4 | SAD 4.3 API | `/attendance/<id>/edit/`, `/leaves/<id>/approve/`, `/reports/generate/` | `/attendance/edit/`, `/leaves/<id>/decide/`, `/reports/class/`, `/reports/shortage/` | Editing works on a whole class + date + hour at once, approve and reject share one URL. Updated in SAD v1.1 |
| 5 | SRS REQ-19 | Approved leave days not counted as absent | On approve, only Absent records in the date range become Leave, Present stays Present. If attendance is marked later for an approved leave day, the student is saved as Leave | Same result for the percentage, and we don't overwrite days the student actually came |
| 6 | SRS REQ-14 | Report download in PDF and Excel | In progress (SEM-16) | Will be updated here when merged |
| 7 | SRS NFR-1 to NFR-3 | Page load / save / report time limits | Not formally measured (TC-15 not run) | No load testing tool set up. Pages are fast on local testing |
| 8 | SRS NFR-4 | Daily database backup | Not automated. Manual backup with `mysqldump -u sams_user -p sams_db > backup.sql` | No server deployment in this project, it runs on our laptops |
| 9 | SAD 3.9 (STRIDE) | Limit login attempts | Not done | Not in the SRS requirements list, left out for time |
| 10 | SRS 2.4, SAD 3.6 | MySQL 8.0 | MySQL for running the app, SQLite (`USE_SQLITE=1`) for local testing and GitHub Actions CI | CI doesn't need a MySQL server, tests run faster |
| 11 | Test Plan 5 | System testing with Selenium | System testing done manually in the browser. 73 automated Django tests run in GitHub Actions on every PR | Not enough time to set up Selenium |
| 12 | Test Plan 7 | Testing 12-10-2026 to 13-11-2026 | Testing done in the two sprints, 19-10 to 23-10 and 26-10 to 30-10-2026 | Sprint dates were given by the course after the Test Plan was submitted. Updated in Test Plan v1.1 |
| 13 | Mark attendance | - | Attendance cannot be marked for a future date | Added as a basic validation |
