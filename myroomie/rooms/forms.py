from django import forms

from accounts.forms import BootstrapMixin

from .models import Room


class RoomForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Room
        exclude = ["owner"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "available_from": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "amenities": forms.CheckboxSelectMultiple,
            "latitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
            "longitude": forms.TextInput(attrs={"readonly": True, "placeholder": "Click the map"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ("latitude", "longitude"):
            self.fields[f].error_messages["required"] = "Please pick the location on the map."
