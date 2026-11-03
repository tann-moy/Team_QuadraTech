from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Preference, UserProfile


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
                continue
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css


class RegisterForm(BootstrapMixin, UserCreationForm):
    name = forms.CharField(max_length=100, label="Full name")
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.RadioSelect, initial="tenant")
    id_type = forms.ChoiceField(choices=UserProfile.ID_TYPES, label="ID type")
    id_document = forms.ImageField(
        label="Photo of your NID / birth certificate",
        help_text="Required. JPG or PNG, max 5 MB. Admin checks it before your account is activated.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ("password1", "password2"):
            self.fields[f].help_text = ""          # any simple password is fine
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"

    def clean_id_document(self):
        image = self.cleaned_data["id_document"]
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image must be smaller than 5 MB.")
        return image

    def save(self, commit=True):
        user = super().save(commit=commit)
        UserProfile.objects.create(
            user=user, name=self.cleaned_data["name"],
            role=self.cleaned_data["role"], phone=self.cleaned_data["phone"],
            id_type=self.cleaned_data["id_type"], id_document=self.cleaned_data["id_document"],
            is_verified=False,           # admin must verify before login
        )
        return user


class UserProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["name", "profile_picture", "organization", "phone", "bio",
                  "ref_loc", "ref_latitude", "ref_longitude"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "ref_latitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
            "ref_longitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
        }


class PreferenceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Preference
        exclude = ["user"]
        widgets = {
            "sleep_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
            "latitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
            "longitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
        }

    def clean(self):
        data = super().clean()
        if data.get("budget_min") is not None and data.get("budget_max") is not None:
            if data["budget_min"] > data["budget_max"]:
                raise forms.ValidationError("Minimum budget cannot be higher than maximum budget.")
        if data.get("latitude") is None or data.get("longitude") is None:
            raise forms.ValidationError("Please select your preferred location on the map.")
        return data


class VerifiedAuthenticationForm(BootstrapMixin, AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        profile = getattr(user, "profile", None)          # superuser has no profile -> allowed
        if profile is not None and not profile.is_verified:
            raise forms.ValidationError(
                "Your account is waiting for admin verification. You can log in after it is approved.",
                code="not_verified")
