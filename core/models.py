from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

class BusinessAccount(models.Model):
    CURRENCIES = [("ARS", "Peso argentino"), ("USD", "Dólar estadounidense"), ("EUR", "Euro"), ("BRL", "Real brasileño"), ("CLP", "Peso chileno"), ("UYU", "Peso uruguayo")]
    RATE_SOURCES = [("BCRA_MINORISTA_VENDEDOR", "BCRA: minorista promedio vendedor"), ("BCRA_MAYORISTA", "BCRA: mayorista de referencia")]
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_account")
    business_name = models.CharField("nombre del negocio", max_length=160)
    must_change_password = models.BooleanField(default=True)
    base_currency = models.CharField("moneda de referencia", max_length=3, choices=CURRENCIES, default="ARS")
    exchange_rate_source = models.CharField("cotización oficial", max_length=32, choices=RATE_SOURCES, default="BCRA_MINORISTA_VENDEDOR")
    is_active = models.BooleanField("cuenta activa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "cuenta de dueño"
        verbose_name_plural = "cuentas de dueños"
        ordering = ["business_name"]
    def __str__(self):
        return self.business_name

class Complex(models.Model):
    account = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name="complexes")
    name = models.CharField("nombre", max_length=160)
    address = models.CharField("dirección", max_length=240, blank=True)
    city = models.CharField("localidad", max_length=120, blank=True)
    province = models.CharField("provincia", max_length=120, blank=True)
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "complejo"
        verbose_name_plural = "complejos"
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["account", "name"], name="unique_complex_name_per_account")]
    def __str__(self):
        return self.name

class Accommodation(models.Model):
    KINDS = [("CABIN", "Cabaña"), ("APARTMENT", "Departamento"), ("HOUSE", "Casa"), ("OTHER", "Otro")]
    account = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name="accommodations")
    complex = models.ForeignKey(Complex, on_delete=models.PROTECT, related_name="accommodations", verbose_name="complejo")
    name = models.CharField("nombre de la unidad", max_length=160)
    kind = models.CharField("tipo", max_length=16, choices=KINDS, default="CABIN")
    capacity = models.PositiveSmallIntegerField("capacidad máxima", default=2)
    bedrooms = models.PositiveSmallIntegerField("dormitorios", default=0)
    beds = models.PositiveSmallIntegerField("camas", default=0)
    size_m2 = models.DecimalField("superficie (m²)", max_digits=7, decimal_places=2, null=True, blank=True)
    description = models.TextField("descripción", blank=True)
    base_nightly_rate = models.DecimalField("tarifa base por noche", max_digits=12, decimal_places=2, default=0)
    base_currency = models.CharField("moneda de tarifa", max_length=3, choices=BusinessAccount.CURRENCIES, default="ARS")
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "alojamiento"
        verbose_name_plural = "alojamientos"
        ordering = ["complex__name", "name"]
        constraints = [models.UniqueConstraint(fields=["account", "complex", "name"], name="unique_accommodation_name_per_complex")]
    def clean(self):
        if self.complex_id and self.account_id and self.complex.account_id != self.account_id:
            raise ValidationError("El complejo seleccionado no pertenece a esta cuenta.")
    def __str__(self):
        return f"{self.name} · {self.complex.name}"

class Guest(models.Model):
    account = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name="guests")
    full_name = models.CharField("nombre y apellido", max_length=180)
    phone = models.CharField("teléfono", max_length=40, blank=True)
    email = models.EmailField("correo electrónico", blank=True)
    document_number = models.CharField("documento", max_length=50, blank=True)
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["full_name"]
    def __str__(self):
        return self.full_name

class PriceRule(models.Model):
    account = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name="price_rules")
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name="price_rules")
    name = models.CharField("nombre de la tarifa", max_length=120, blank=True)
    guest_count = models.PositiveSmallIntegerField("cantidad de huéspedes", null=True, blank=True, help_text="Dejar vacío para cualquier cantidad.")
    valid_from = models.DateField("desde", null=True, blank=True)
    valid_until = models.DateField("hasta", null=True, blank=True)
    nightly_rate = models.DecimalField("precio por noche", max_digits=12, decimal_places=2)
    currency = models.CharField("moneda", max_length=3, choices=BusinessAccount.CURRENCIES, default="ARS")
    minimum_nights = models.PositiveSmallIntegerField("mínimo de noches", default=1)
    is_active = models.BooleanField("activa", default=True)
    class Meta:
        ordering = ["accommodation__name", "valid_from", "guest_count"]
        verbose_name = "regla de precio"
        verbose_name_plural = "reglas de precios"
    def clean(self):
        if self.accommodation_id and self.account_id and self.accommodation.account_id != self.account_id:
            raise ValidationError("El alojamiento no pertenece a esta cuenta.")
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError("La fecha final debe ser igual o posterior a la inicial.")
        if self.guest_count and self.accommodation_id and self.guest_count > self.accommodation.capacity:
            raise ValidationError("La cantidad de huéspedes supera la capacidad del alojamiento.")
    def __str__(self):
        return self.name or f"{self.accommodation}: {self.guest_count or 'todos'} huéspedes"

class Reservation(models.Model):
    STATUSES = [("PENDING", "Pendiente"), ("CONFIRMED", "Confirmada"), ("CHECKED_IN", "En estadía"), ("COMPLETED", "Finalizada"), ("CANCELLED", "Cancelada")]
    account = models.ForeignKey(BusinessAccount, on_delete=models.CASCADE, related_name="reservations")
    accommodation = models.ForeignKey(Accommodation, on_delete=models.PROTECT, related_name="reservations")
    guest = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name="reservations")
    check_in = models.DateField("ingreso")
    check_out = models.DateField("egreso")
    guest_count = models.PositiveSmallIntegerField("huéspedes")
    status = models.CharField("estado", max_length=16, choices=STATUSES, default="CONFIRMED")
    total_price = models.DecimalField("importe acordado", max_digits=12, decimal_places=2)
    currency = models.CharField("moneda", max_length=3, choices=BusinessAccount.CURRENCIES, default="ARS")
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["check_in", "accommodation__name"]
    @property
    def nights(self):
        return (self.check_out - self.check_in).days
    def clean(self):
        errors = {}
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            errors["check_out"] = "La salida debe ser posterior al ingreso."
        if self.accommodation_id and self.account_id and self.accommodation.account_id != self.account_id:
            errors["accommodation"] = "El alojamiento no pertenece a esta cuenta."
        if self.guest_id and self.account_id and self.guest.account_id != self.account_id:
            errors["guest"] = "El huésped no pertenece a esta cuenta."
        if self.guest_count and self.accommodation_id and self.guest_count > self.accommodation.capacity:
            errors["guest_count"] = "La cantidad supera la capacidad del alojamiento."
        if self.check_in and self.check_out and self.accommodation_id and self.status != "CANCELLED":
            overlap = Reservation.objects.filter(
                account_id=self.account_id, accommodation_id=self.accommodation_id,
                status__in=["PENDING", "CONFIRMED", "CHECKED_IN"],
                check_in__lt=self.check_out, check_out__gt=self.check_in,
            )
            if self.pk:
                overlap = overlap.exclude(pk=self.pk)
            if overlap.exists():
                errors["check_in"] = "Ese alojamiento ya tiene una reserva que se superpone con esas fechas."
        if errors:
            raise ValidationError(errors)
    @property
    def paid_amount(self):
        from decimal import Decimal
        return sum(self.payments.values_list("reservation_amount", flat=True), Decimal("0.00"))

    @property
    def balance_due(self):
        return self.total_price - self.paid_amount

    def __str__(self):
        return f"{self.accommodation} · {self.check_in}–{self.check_out}"
