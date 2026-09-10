from django import forms

from .models import User


class AccountCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmation du mot de passe", widget=forms.PasswordInput)

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

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Les deux mots de passe doivent être identiques.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user