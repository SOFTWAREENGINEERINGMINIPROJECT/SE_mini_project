from django.contrib import admin

from .models import ClassSection, Subject, Teaching


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """SEM-9 / REQ-5: code is unique at DB level (Subject.code unique=True)."""
    list_display = ("code", "name", "semester")
    list_filter = ("semester",)
    search_fields = ("code", "name")


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    """SEM-10 / REQ-6: unique on department + semester + section."""
    list_display = ("department", "semester", "section", "student_count")
    list_filter = ("department", "semester")
    filter_horizontal = ("students",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # only students can be put in a class
        if db_field.name == "students":
            kwargs["queryset"] = db_field.related_model.objects.filter(role="student")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Students")
    def student_count(self, obj):
        return obj.students.count()


@admin.register(Teaching)
class TeachingAdmin(admin.ModelAdmin):
    """SEM-10 / REQ-7: unique on subject + class_section."""
    list_display = ("subject", "class_section", "faculty")
    list_filter = ("class_section", "subject")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # only faculty can be assigned to teach
        if db_field.name == "faculty":
            kwargs["queryset"] = db_field.related_model.objects.filter(role="faculty")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
