from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

from .models import Accommodation, BusinessAccount, Complex

class OwnerLoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Tu usuario"}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Tu contraseña"}))

class OwnerPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    new_password2 = forms.CharField(label="Repetir nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

class ComplexForm(forms.ModelForm):
    class Meta:
        model = Complex
        fields = ["name", "address", "city", "province", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

class AccommodationForm(forms.ModelForm):
    class Meta:
        model = Accommodation
        fields = ["complex", "name", "kind", "capacity", "bedrooms", "beds", "size_m2", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = account
        self.fields["complex"].queryset = Complex.objects.filter(account=account).order_by("name")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.account = self.account
        if commit:
            obj.full_clean()
            obj.save()
        return obj

class CreateOwnerForm(forms.Form):
    business_name = forms.CharField(label="Nombre del negocio", max_length=160)
    username = forms.CharField(label="Usuario de acceso", max_length=150)
    email = forms.EmailField(label="Correo electrónico")

    def clean_username(self):
        value = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError("Ese usuario ya existe.")
        return value

    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("Ese correo ya está registrado.")
        return value

    def create_owner(self):
        password = get_random_string(16)
        user = User.objects.create_user(username=self.cleaned_data["username"], email=self.cleaned_data["email"], password=password)
        account = BusinessAccount.objects.create(owner=user, business_name=self.cleaned_data["business_name"], must_change_password=True)
        return account, password
