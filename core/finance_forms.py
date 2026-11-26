from django import forms
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import BusinessAccount, Accommodation, Reservation
from .finance_models import Payment, Expense, ExpenseAllocation, InventoryItem, InventoryMovement
from .services.exchange import convert_currency
from django.utils import timezone

class PaymentForm(forms.ModelForm):
    amount=forms.DecimalField(label="Importe recibido",max_digits=14,decimal_places=2,min_value=Decimal("0.01"))
    class Meta:
        model=Payment; fields=["reservation","amount","currency","method","paid_on","reference"]
        widgets={"paid_on":forms.DateInput(attrs={"type":"date"})}
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["reservation"].queryset=Reservation.objects.filter(account=account).exclude(status="CANCELLED").select_related("accommodation","guest")
        self.fields["paid_on"].initial=timezone.localdate()
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account
        obj.reservation_currency=obj.reservation.currency; obj.base_currency=self.account.base_currency
        source=self.account.exchange_rate_source
        obj.reservation_amount,obj.exchange_rate,obj.quote_date,obj.quote_source=convert_currency(obj.amount,obj.currency,obj.reservation_currency,obj.paid_on,source)
        obj.base_amount,_,_,_=convert_currency(obj.amount,obj.currency,obj.base_currency,obj.paid_on,source)
        if commit: obj.full_clean(); obj.save()
        return obj

class ExpenseForm(forms.ModelForm):
    amount=forms.DecimalField(label="Importe",max_digits=14,decimal_places=2,min_value=Decimal("0.01"))
    class Meta:
        model=Expense; fields=["accommodation","category","detail","spent_on","amount","currency"]
        widgets={"spent_on":forms.DateInput(attrs={"type":"date"})}
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["accommodation"].queryset=Accommodation.objects.filter(account=account,is_active=True)
        self.fields["accommodation"].required=False
        self.fields["spent_on"].initial=timezone.localdate()
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account; obj.base_currency=self.account.base_currency
        obj.base_amount,obj.exchange_rate,obj.quote_date,obj.quote_source=convert_currency(obj.amount,obj.currency,obj.base_currency,obj.spent_on,self.account.exchange_rate_source)
        if commit: obj.full_clean(); obj.save()
        return obj

class ExpenseAllocationForm(forms.ModelForm):
    amount_base=forms.DecimalField(label="Importe asignado",max_digits=14,decimal_places=2,min_value=Decimal("0.01"))
    class Meta:
        model=ExpenseAllocation; fields=["expense","accommodation","amount_base"]
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["expense"].queryset=Expense.objects.filter(account=account,accommodation__isnull=True)
        self.fields["accommodation"].queryset=Accommodation.objects.filter(account=account,is_active=True)
    def clean(self):
        data=super().clean(); expense=data.get("expense"); amount=data.get("amount_base")
        if expense and amount:
            allocated=sum((x.amount_base for x in expense.allocations.all()),start=0)
            if allocated+amount>expense.base_amount: raise ValidationError("La distribución no puede superar el importe total del gasto general.")
        return data

class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model=BusinessAccount
        fields=["base_currency","exchange_rate_source"]

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model=InventoryItem; fields=["accommodation","name","category","unit_label","track_per_stay","clean_quantity"]
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["accommodation"].queryset=Accommodation.objects.filter(account=account,is_active=True)
    def save(self,commit=True):
        obj=super().save(commit=False); obj.account=self.account
        if commit: obj.full_clean(); obj.save()
        return obj

class InventoryMovementForm(forms.Form):
    item=forms.ModelChoiceField(queryset=InventoryItem.objects.none(),label="Elemento")
    movement_type=forms.ChoiceField(choices=InventoryMovement.TYPES,label="Movimiento")
    quantity=forms.IntegerField(min_value=1,label="Cantidad")
    reservation=forms.ModelChoiceField(queryset=Reservation.objects.none(),required=False,label="Estadía (opcional)")
    source_state=forms.ChoiceField(choices=[("","—"),*InventoryMovement.STATES],required=False,label="Estado actual")
    notes=forms.CharField(max_length=240,required=False,label="Nota")
    def __init__(self,*args,account=None,**kwargs):
        super().__init__(*args,**kwargs); self.account=account
        self.fields["item"].queryset=InventoryItem.objects.filter(account=account,is_active=True).select_related("accommodation")
        self.fields["reservation"].queryset=Reservation.objects.filter(account=account).exclude(status="CANCELLED").select_related("accommodation")

    def clean(self):
        data=super().clean()
        item=data.get("item"); reservation=data.get("reservation")
        if item and item.track_per_stay and not reservation:
            self.add_error("reservation","Este elemento requiere asociar cada movimiento con una estadía.")
        if item and reservation and reservation.accommodation_id!=item.accommodation_id:
            self.add_error("reservation","La estadía seleccionada pertenece a otro alojamiento.")
        return data
