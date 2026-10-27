from datetime import date

from django import forms

from academics.models import Teaching

HOURS = [(h, f"Hour {h}") for h in range(1, 9)]


class SelectClassForm(forms.Form):
    """Step 1 of marking: which subject + class, which date and hour."""
    teaching = forms.ModelChoiceField(queryset=Teaching.objects.none(), label="Subject / class")
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), initial=date.today)
    hour = forms.TypedChoiceField(choices=HOURS, coerce=int)

    def __init__(self, *args, faculty=None, all_classes=False, **kwargs):
        super().__init__(*args, **kwargs)
        # a faculty member can only mark classes they are assigned to (BR-2);
        # all_classes is for admins editing old attendance (BR-3)
        qs = Teaching.objects.all() if all_classes else Teaching.objects.filter(faculty=faculty)
        self.fields["teaching"].queryset = qs.select_related("subject", "class_section", "faculty")
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-select" if isinstance(f, (forms.ModelChoiceField, forms.TypedChoiceField)) else "form-control")

    def clean_date(self):
        d = self.cleaned_data["date"]
        if d > date.today():
            raise forms.ValidationError("Cannot mark attendance for a future date.")
        return d
