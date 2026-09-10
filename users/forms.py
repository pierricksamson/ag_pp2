from django import forms
from django.utils.crypto import get_random_string

from academics.models import ClassGroup

from .models import StudentProfile, User


class AccountCreationForm(forms.ModelForm):
    class_group = forms.ModelChoiceField(label="Classe de l'élève", queryset=ClassGroup.objects.none(), required=False)
    teacher_classes = forms.ModelMultipleChoiceField(label="Classes du professeur", queryset=ClassGroup.objects.none(), required=False)
    children = forms.ModelMultipleChoiceField(label="Enfants rattachés", queryset=StudentProfile.objects.none(), required=False)
    password1 = forms.CharField(required=False, widget=forms.HiddenInput)
    password2 = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "role", "is_active")
        labels = {
            "email": "Adresse email",
            "first_name": "Prénom",
            "last_name": "Nom",
            "phone": "Téléphone",
            "role": "Fonction",
            "is_active": "Compte actif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].widget.attrs["x-model"] = "role"
        classes = ClassGroup.objects.select_related("level", "academic_year").order_by("level__order", "name")
        self.fields["class_group"].queryset = classes
        self.fields["teacher_classes"].queryset = classes
        self.fields["children"].queryset = StudentProfile.objects.select_related("user", "class_group__level").order_by("user__last_name", "user__first_name")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") and cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Les deux mots de passe doivent être identiques.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1") or get_random_string(14)
        user.set_password(password)
        self.generated_password = password
        if commit:
            user.save()
        return user