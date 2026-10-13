# Student Attendance Management System (SAMS)

Django web app for recording and tracking student attendance. Built for UE24CS341A (Software Engineering) at PES University, Team 1.

## Modules

| App | What it covers |
|---|---|
| `accounts` | Custom user model and roles |
| `academics` | Class sections, subjects, teaching assignments |
| `attendance` | Attendance records and audit log |
| `leaves` | Leave requests |
| `reports` | Attendance reports (PDF/Excel export) |

## Stack

Django 4.2, MySQL (SQLite optional for local dev), ReportLab, openpyxl.

## Setup

```bash
cd sams
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create `sams/.env`:

```
SECRET_KEY=change-me
DB_NAME=sams_db
DB_USER=sams_user
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
EMAIL_USER=
EMAIL_PASS=
```

No MySQL handy? Set `USE_SQLITE=1` instead.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docs

`docs/` has the SRS, SAD and Software Test Plan (PDF + DOCX).
