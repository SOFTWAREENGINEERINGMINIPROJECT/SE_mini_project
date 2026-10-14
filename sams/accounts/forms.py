from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """AuthenticationForm with Bootstrap styling and the wording the SRS stimulus/response table expects."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Invalid username or password.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
