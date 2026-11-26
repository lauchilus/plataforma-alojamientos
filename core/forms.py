from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.utils.crypto import get_random_string
from .models import Accommodation, BusinessAccount, Complex, PriceRule, Reservation, Guest
from .services.pricing import quote_reservation

class OwnerLoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autocomplete":"username","placeholder":"Tu usuario"}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput(attrs={"autocomplete":"current-password","placeholder":"Tu contraseña"}))
class OwnerPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput(attrs={"autocomplete":"current-password"}))
    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete":"new-password"}))
    new_password2 = forms.CharField(label="Repetir nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete":"new-password"}))
class ComplexForm(forms.ModelForm):
    class Meta:
        model=Complex; fields=["name","address","city","province","notes"]
        widgets={"notes":forms.Textarea(attrs={"rows":3})}
class AccommodationForm(forms.ModelForm):
    class Meta:
        model=Accommodation; fields=["complex","name","kind","capacity","bedrooms","beds","size_m2","description","base_nightly_rate","base_currency","is_active"]
        widgets={"description":forms.Textarea(attrs={"rows":3})}
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["complex"].queryset=Complex.objects.filter(account=account).order_by("name")
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account
        if commit: obj.full_clean(); obj.save()
        return obj
class PriceRuleForm(forms.ModelForm):
    nightly_rate=forms.DecimalField(label="Precio por noche",max_digits=12,decimal_places=2,min_value=Decimal("0.01"))
    guest_count=forms.IntegerField(label="Cantidad de huéspedes",min_value=1,required=False)
    minimum_nights=forms.IntegerField(label="Mínimo de noches",min_value=1)
    class Meta:
        model=PriceRule; fields=["accommodation","name","guest_count","valid_from","valid_until","nightly_rate","currency","minimum_nights","is_active"]
        widgets={"valid_from":forms.DateInput(attrs={"type":"date"}),"valid_until":forms.DateInput(attrs={"type":"date"})}
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["accommodation"].queryset=Accommodation.objects.filter(account=account,is_active=True).order_by("name")
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account
        if commit: obj.full_clean(); obj.save()
        return obj
class ReservationForm(forms.ModelForm):
    guest_count=forms.IntegerField(label="Huéspedes",min_value=1)
    agreed_price=forms.DecimalField(label="Importe acordado",max_digits=12,decimal_places=2,min_value=Decimal("0.01"),required=False,help_text="Dejar vacío para usar el precio calculado.")
    guest_name=forms.CharField(label="Nombre y apellido",max_length=180)
    guest_phone=forms.CharField(label="Teléfono",max_length=40,required=False)
    guest_email=forms.EmailField(label="Correo electrónico",required=False)
    guest_document=forms.CharField(label="Documento",max_length=50,required=False)
    class Meta:
        model=Reservation
        fields=["accommodation","check_in","check_out","guest_count","status","currency","notes"]
        widgets={"check_in":forms.DateInput(attrs={"type":"date"}),"check_out":forms.DateInput(attrs={"type":"date"}),"notes":forms.Textarea(attrs={"rows":3})}
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["accommodation"].queryset=Accommodation.objects.filter(account=account,is_active=True).select_related("complex").order_by("complex__name","name")
        if self.instance.pk:
            self.fields["guest_name"].initial=self.instance.guest.full_name
            self.fields["guest_phone"].initial=self.instance.guest.phone
            self.fields["guest_email"].initial=self.instance.guest.email
            self.fields["guest_document"].initial=self.instance.guest.document_number
            self.fields["agreed_price"].initial=self.instance.total_price
    def clean(self):
        data=super().clean()
        acc=data.get("accommodation"); checkin=data.get("check_in"); checkout=data.get("check_out"); count=data.get("guest_count")
        manual=data.get("agreed_price")
        if acc and checkin and checkout and count and not manual:
            try:
                amount,currency,_=quote_reservation(acc,checkin,checkout,count)
                data["calculated_price"]=amount; data["calculated_currency"]=currency
            except ValidationError as exc:
                self.add_error("agreed_price",exc)
        return data
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account
        with transaction.atomic():
            guest=obj.guest if obj.pk else Guest(account=self.account)
            guest.account=self.account
            guest.full_name=self.cleaned_data["guest_name"]
            guest.phone=self.cleaned_data["guest_phone"]
            guest.email=self.cleaned_data["guest_email"]
            guest.document_number=self.cleaned_data["guest_document"]
            guest.save()
            obj.guest=guest
            if self.cleaned_data.get("agreed_price"):
                obj.total_price=self.cleaned_data["agreed_price"]
            else:
                obj.total_price=self.cleaned_data["calculated_price"]
                obj.currency=self.cleaned_data["calculated_currency"]
            if commit:
                obj.full_clean()
                obj.save()
        return obj
class CreateOwnerForm(forms.Form):
    business_name=forms.CharField(label="Nombre del negocio",max_length=160)
    username=forms.CharField(label="Usuario de acceso",max_length=150)
    email=forms.EmailField(label="Correo electrónico")
    def clean_username(self):
        value=self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=value).exists(): raise ValidationError("Ese usuario ya existe.")
        return value
    def clean_email(self):
        value=self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists(): raise ValidationError("Ese correo ya está registrado.")
        return value
    def create_owner(self):
        password=get_random_string(16)
        user=User.objects.create_user(username=self.cleaned_data["username"],email=self.cleaned_data["email"],password=password)
        account=BusinessAccount.objects.create(owner=user,business_name=self.cleaned_data["business_name"],must_change_password=True)
        return account,password
