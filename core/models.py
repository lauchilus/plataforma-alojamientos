from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

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
