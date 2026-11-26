from django.core.exceptions import ValidationError
from django.db import models
from .models import BusinessAccount, Accommodation, Reservation

class Payment(models.Model):
    METHODS=[("CASH","Efectivo"),("TRANSFER","Transferencia"),("CARD","Tarjeta"),("MERCADO_PAGO","Mercado Pago"),("OTHER","Otro")]
    account=models.ForeignKey(BusinessAccount,on_delete=models.CASCADE,related_name="payments")
    reservation=models.ForeignKey(Reservation,on_delete=models.CASCADE,related_name="payments")
    amount=models.DecimalField("importe recibido",max_digits=14,decimal_places=2)
    currency=models.CharField("moneda recibida",max_length=3,choices=BusinessAccount.CURRENCIES)
    method=models.CharField("medio de pago",max_length=20,choices=METHODS,default="TRANSFER")
    paid_on=models.DateField("fecha de cobro")
    reservation_amount=models.DecimalField("equivalente en moneda de reserva",max_digits=14,decimal_places=2)
    reservation_currency=models.CharField(max_length=3,choices=BusinessAccount.CURRENCIES)
    base_amount=models.DecimalField("equivalente en moneda de referencia",max_digits=14,decimal_places=2)
    base_currency=models.CharField(max_length=3,choices=BusinessAccount.CURRENCIES)
    exchange_rate=models.DecimalField("tasa aplicada",max_digits=18,decimal_places=8,default=1)
    quote_date=models.DateField("fecha de cotización",null=True,blank=True)
    quote_source=models.CharField("fuente",max_length=120,blank=True)
    reference=models.CharField("referencia",max_length=160,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-paid_on","-id"]
    def clean(self):
        if self.reservation_id and self.account_id and self.reservation.account_id!=self.account_id: raise ValidationError("La reserva no pertenece a esta cuenta.")
    def __str__(self): return f"{self.amount} {self.currency} · {self.reservation}"

class Expense(models.Model):
    account=models.ForeignKey(BusinessAccount,on_delete=models.CASCADE,related_name="expenses")
    accommodation=models.ForeignKey(Accommodation,on_delete=models.PROTECT,related_name="expenses",null=True,blank=True,verbose_name="alojamiento (opcional)")
    category=models.CharField("categoría",max_length=100)
    detail=models.CharField("detalle",max_length=240)
    spent_on=models.DateField("fecha")
    amount=models.DecimalField("importe",max_digits=14,decimal_places=2)
    currency=models.CharField("moneda",max_length=3,choices=BusinessAccount.CURRENCIES)
    base_amount=models.DecimalField("equivalente en moneda de referencia",max_digits=14,decimal_places=2)
    base_currency=models.CharField(max_length=3,choices=BusinessAccount.CURRENCIES)
    exchange_rate=models.DecimalField("tasa aplicada",max_digits=18,decimal_places=8,default=1)
    quote_date=models.DateField("fecha de cotización",null=True,blank=True)
    quote_source=models.CharField("fuente",max_length=120,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-spent_on","-id"]
    def clean(self):
        if self.accommodation_id and self.account_id and self.accommodation.account_id!=self.account_id: raise ValidationError("El alojamiento no pertenece a esta cuenta.")
    @property
    def is_general(self): return self.accommodation_id is None
    def __str__(self): return f"{self.category}: {self.detail}"

class ExpenseAllocation(models.Model):
    expense=models.ForeignKey(Expense,on_delete=models.CASCADE,related_name="allocations")
    accommodation=models.ForeignKey(Accommodation,on_delete=models.CASCADE,related_name="expense_allocations")
    amount_base=models.DecimalField("importe asignado",max_digits=14,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["expense","accommodation"],name="unique_expense_allocation_per_accommodation")]
    def clean(self):
        if self.expense_id and self.accommodation_id and self.expense.account_id!=self.accommodation.account_id: raise ValidationError("El alojamiento y el gasto deben ser de la misma cuenta.")
        if self.expense_id and self.expense.accommodation_id: raise ValidationError("Solo se pueden distribuir gastos generales.")

class InventoryItem(models.Model):
    account=models.ForeignKey(BusinessAccount,on_delete=models.CASCADE,related_name="inventory_items")
    accommodation=models.ForeignKey(Accommodation,on_delete=models.CASCADE,related_name="inventory_items")
    name=models.CharField("elemento",max_length=140)
    category=models.CharField("categoría",max_length=80,blank=True)
    unit_label=models.CharField("unidad",max_length=30,default="unidad")
    track_per_stay=models.BooleanField("registrar entregas y devoluciones por estadía",default=False)
    clean_quantity=models.PositiveIntegerField("limpias / disponibles",default=0)
    in_use_quantity=models.PositiveIntegerField("entregadas / en uso",default=0)
    used_quantity=models.PositiveIntegerField("usadas / por limpiar",default=0)
    damaged_quantity=models.PositiveIntegerField("dañadas",default=0)
    missing_quantity=models.PositiveIntegerField("faltantes",default=0)
    is_active=models.BooleanField("activo",default=True)
    class Meta:
        ordering=["accommodation__name","name"]
        constraints=[models.UniqueConstraint(fields=["accommodation","name"],name="unique_inventory_item_per_accommodation")]
    def clean(self):
        if self.accommodation_id and self.account_id and self.accommodation.account_id!=self.account_id: raise ValidationError("El alojamiento no pertenece a esta cuenta.")
    def __str__(self): return f"{self.name} · {self.accommodation}"

class InventoryMovement(models.Model):
    TYPES=[("DELIVER_CLEAN","Entrega limpia"),("REPLACEMENT","Reposición limpia"),("RETURN_USED","Retiro de usada"),("LAUNDRY_CLEAN","Regreso limpia"),("DAMAGE","Marcar dañada"),("MISSING","Marcar faltante"),("STOCK_IN","Ingreso de stock")]
    STATES=[("clean","limpia/disponible"),("in_use","entregada/en uso"),("used","usada/por limpiar")]
    account=models.ForeignKey(BusinessAccount,on_delete=models.CASCADE,related_name="inventory_movements")
    item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name="movements")
    reservation=models.ForeignKey(Reservation,on_delete=models.SET_NULL,related_name="inventory_movements",null=True,blank=True)
    movement_type=models.CharField("movimiento",max_length=20,choices=TYPES)
    quantity=models.PositiveIntegerField("cantidad")
    source_state=models.CharField("estado de origen",max_length=12,choices=STATES,blank=True)
    notes=models.CharField("nota",max_length=240,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-created_at"]
    def clean(self):
        if self.item_id and self.account_id and self.item.account_id!=self.account_id: raise ValidationError("El elemento no pertenece a esta cuenta.")
        if self.reservation_id and self.item_id and (self.reservation.account_id!=self.account_id or self.reservation.accommodation_id!=self.item.accommodation_id): raise ValidationError("La estadía no pertenece a este alojamiento.")
