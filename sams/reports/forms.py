from datetime import date

from django import forms

from academics.models import Teaching


class ReportForm(forms.Form):
    """REQ-13: pick a class + subject and a date range."""
    teaching = forms.ModelChoiceField(queryset=Teaching.objects.none(), label="Subject / class")
    start = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="From")
    end = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="To", initial=date.today)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Teaching.objects.select_related("subject", "class_section", "faculty")
        if user is not None and user.role == "faculty":
            qs = qs.filter(faculty=user)  # faculty only report on their own classes
        self.fields["teaching"].queryset = qs
        for f in self.fields.values():
            f.widget.attrs.setdefault(
                "class", "form-select" if isinstance(f, forms.ModelChoiceField) else "form-control"
            )

    def clean(self):
        data = super().clean()
        start, end = data.get("start"), data.get("end")
        if start and end and start > end:
            raise forms.ValidationError("'From' date must be on or before 'To' date.")
        return data