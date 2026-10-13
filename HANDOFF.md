# Handoff - SAMS code (Sprint 1)

What Gyaan has set up so far and what each of us picks up next. Read this once before you start coding.

## Done

| Jira | What |
|---|---|
| SEM-18 | Django 4.2 project, 5 apps created, MySQL config through `.env`, `.gitignore` |
| SEM-19 | Shared models for all apps + migrations + admin registration |

Docs (SRS, SAD, Test Plan) are in `docs/`. REQ / NFR numbers below refer to the SRS.

## Getting it running

Steps are in `README.md`. Quick version:

```bash
git clone https://github.com/GyaanShetty/StudentAttendanceManagementSystem.git
cd StudentAttendanceManagementSystem/sams
python3 -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
# make sams/.env (see README), then:
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # http://127.0.0.1:8000/admin
```

- No MySQL yet? Run with `USE_SQLITE=1` in front of the command, e.g. `USE_SQLITE=1 python manage.py migrate`.
- On Mac with conda, do `conda deactivate` first or MySQL / mysqlclient gets confused.
- `mysqlclient` won't install on Windows? `pip install pymysql` and put these 2 lines at the top of `sams/sams/__init__.py` (don't commit that):
  ```python
  import pymysql
  pymysql.install_as_MySQLdb()
  ```

## What's in settings.py

- `AUTH_USER_MODEL = 'accounts.User'` - always use `settings.AUTH_USER_MODEL` / `get_user_model()`, never `django.contrib.auth.models.User`
- Session expires after 30 min idle (NFR-9)
- Gmail SMTP configured from `EMAIL_USER` / `EMAIL_PASS` in `.env`. While testing, you can use `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in your local settings so mails just print in the terminal
- `LOGIN_URL` points to `/admin/login/` for now - change it to `/accounts/login/` once SEM-5 is done
- Timezone is Asia/Kolkata

## Models (don't change these without telling everyone)

**accounts.User** (extends Django's AbstractUser)
- `role`: `"admin" | "faculty" | "student"`
- `srn` (unique, can be empty for faculty/admin), `phone`

**academics**
- `ClassSection`: `department`, `semester`, `section`, `students` (M2M to User). Unique on dept+sem+section
- `Subject`: `code` (unique), `name`, `semester`
- `Teaching`: `faculty`, `subject`, `class_section` - which faculty teaches which subject to which class. Unique on subject+class

**attendance**
- `AttendanceRecord`: `student`, `subject`, `class_section`, `date`, `hour`, `status` (`"P"`, `"A"`, `"L"`), `marked_by`, `marked_at`
  - unique on student+subject+date+hour (REQ-9, so duplicates fail at DB level too)
- `AttendanceLog`: `record`, `changed_by`, `old_status`, `new_status`, `changed_at` - create one on every edit (NFR-11)

**leaves**
- `LeaveRequest`: `student`, `from_date`, `to_date`, `reason`, `status` (`"pending" | "approved" | "rejected"`), `created_at`

**reports** - no models, it only reads attendance data.

If you need a new field, add it, run `makemigrations`, and commit the migration file with it. Tell the group first so we don't get two conflicting migrations in one app.

## How we work

- Branch per story: `git checkout -b SEM-11-mark-attendance`
- Commit messages start with the Jira key: `SEM-11: mark attendance page`
- Pull `main` before you start every day: `git pull origin main`
- Open a PR into `main`, someone else reviews, then merge. Nobody pushes straight to `main`
- Move your Jira story To Do -> In Progress -> Done as you go (screenshots of the board are needed for evaluation)
- Each app gets its own `urls.py`, `templates/<app>/` folder and `tests.py`
- Put views behind `@login_required` and check `request.user.role` (NFR-7)

## Who does what next

### Santosh - accounts (SEM-1)
1. **SEM-5** login / logout: use Django's `LoginView` / `LogoutView`, template `accounts/login.html`. Add `path('accounts/', include('accounts.urls'))` to `sams/urls.py`
2. **SEM-6** role dashboard: after login, redirect by `user.role`. Make a small `role_required("faculty")` decorator in `accounts/decorators.py` that the others can import
3. **SEM-7** add / edit / delete students and faculty (admin only)
4. **SEM-8** Excel upload with openpyxl, columns as in SRS Appendix B; show rejected rows with the reason

Do the decorator first - everyone else needs it.

### Deepak - academics + attendance (SEM-2)
1. **SEM-9, SEM-10** pages to add subjects and classes and assign faculty (or just use Django admin for Sprint 1 and build pages in Sprint 2)
2. **SEM-11** mark attendance at `/attendance/mark/`: pick subject + class + date + hour, list students (everyone Present by default), tick absentees, save. Wrap the save in `transaction.atomic()`; catch `IntegrityError` and show "Attendance already marked"
3. **SEM-12** edit within 3 days only, and write an `AttendanceLog` row on every change
4. **SEM-13** put the percentage function in `attendance/utils.py` so reports and leaves can use the same one:
   ```python
   def attendance_percent(student, subject):
       # (P + L) / total * 100, rounded to 2 decimals; 0 if no classes yet
   ```
   After saving a class, call `check_shortage(student, subject)` from `leaves/utils.py` (Gyaan writes it) for each student

### Subhransi - reports (SEM-3)
1. **SEM-14** `/reports/my/` - student sees subject, conducted, attended, %. Only for `request.user`, never take a student id from the URL (NFR-8)
2. **SEM-15** report for class + subject + date range
3. **SEM-16** PDF (reportlab) and Excel (openpyxl) download - fields as in SRS Appendix B
4. **SEM-17** shortage list (< 75%)

Use `attendance_percent()` from `attendance/utils.py` - don't write a second copy of the formula.

### Gyaan - leaves (SEM-4)
1. **SEM-20** `leaves/utils.py: check_shortage(student, subject)` - if % < 75, `send_mail` to `student.email`
2. **SEM-21** apply leave form
3. **SEM-22** faculty approve / reject; on approve, set matching `AttendanceRecord`s in that date range to `"L"`

## Known loose ends

- `sams/urls.py` only has `/admin/` right now - each of us adds our own `include(...)` line (small merge conflicts there are normal, just keep all the lines)
- No base template yet. First person to need one: make `templates/base.html` with a Bootstrap 5 CDN link and nav bar, and set `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']`
- `tests.py` files are all empty - test cases to implement are in the Test Plan (`docs/Test_Plan_Team1_SAMS.pdf`, TC-01 to TC-17)
- `.env` is not in git. Everyone makes their own. Never commit passwords

## Sprint 1 (5 - 18 Oct) target

SEM-5, 6, 9, 10, 11, 14, 18 (done), 19 (done). Rest goes to Sprint 2.
