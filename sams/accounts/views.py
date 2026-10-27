from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .decorators import role_required
from .importer import COLUMNS, BadWorkbook, import_students


@login_required
def dashboard(request):
    """Land every role on its own dashboard template after login (REQ-2)."""
    return render(request, f"accounts/dashboard_{request.user.role}.html")


# ---- SEM-8 (REQ-4): Excel upload for students ----

@role_required("admin")
def upload_students(request):
    """Admin uploads an .xlsx of students; valid rows are saved, rejected rows are listed with the reason."""
    result = None
    if request.method == "POST":
        f = request.FILES.get("file")
        if not f:
            messages.error(request, "Choose an Excel (.xlsx) file first.")
        elif not f.name.lower().endswith(".xlsx"):
            messages.error(request, "Only .xlsx files are accepted.")
        else:
            try:
                result = import_students(f)
            except BadWorkbook as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"{len(result['created'])} student(s) added, {len(result['rejected'])} row(s) rejected.",
                )
    return render(request, "accounts/upload_students.html", {"result": result, "columns": COLUMNS})
