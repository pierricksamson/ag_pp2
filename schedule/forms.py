from django import forms

from .models import CourseSession
from .services import validate_session_conflicts


class CourseSessionForm(forms.ModelForm):
    class Meta:
        model = CourseSession
        fields = ("title", "class_groups", "subject", "teacher", "room", "day", "start_time", "end_time", "color")
        widgets = {
                     "start_time"   : forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
                     "end_time"     : forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
                  }

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        session = self.instance
        for field, value in cleaned_data.items():
            if field != "class_groups":
                setattr(session, field, value)

        validate_session_conflicts(session, class_group_ids=cleaned_data["class_groups"].values_list("id", flat=True))
        return cleaned_data
