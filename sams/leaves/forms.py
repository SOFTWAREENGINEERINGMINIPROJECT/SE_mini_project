from datetime import date

from django import forms

from .models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    """SEM-21 (REQ-17): student gives the dates and a reason."""

    class Meta:
        model = LeaveRequest
        fields = ["from_date", "to_date", "reason"]
        widgets = {
            "from_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "to_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reason": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 5:
            raise forms.ValidationError("Please give a proper reason.")
        return reason

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("from_date"), cleaned.get("to_date")
        if start and end:
            if end < start:
                raise forms.ValidationError("To date cannot be before from date.")
            if (end - start).days > 30:
                raise forms.ValidationError("Leave cannot be longer than 30 days.")
            if self.student is not None:
                overlap = LeaveRequest.objects.filter(
                    student=self.student,
                    status__in=["pending", "approved"],
                    from_date__lte=end,
                    to_date__gte=start,
                ).exists()
                if overlap:
                    raise forms.ValidationError("You already have a leave request for these dates.")
        return cleaned
