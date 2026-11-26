# Generated for the initial owner/property catalog.
import django.conf
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="BusinessAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("business_name", models.CharField(max_length=160, verbose_name="nombre del negocio")),
                ("must_change_password", models.BooleanField(default=True)),
                ("base_currency", models.CharField(choices=[("ARS", "Peso argentino"), ("USD", "Dólar estadounidense"), ("EUR", "Euro"), ("BRL", "Real brasileño"), ("CLP", "Peso chileno"), ("UYU", "Peso uruguayo")], default="ARS", max_length=3, verbose_name="moneda de referencia")),
                ("exchange_rate_source", models.CharField(choices=[("BCRA_MINORISTA_VENDEDOR", "BCRA: minorista promedio vendedor"), ("BCRA_MAYORISTA", "BCRA: mayorista de referencia")], default="BCRA_MINORISTA_VENDEDOR", max_length=32, verbose_name="cotización oficial")),
                ("is_active", models.BooleanField(default=True, verbose_name="cuenta activa")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="business_account", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "cuenta de dueño", "verbose_name_plural": "cuentas de dueños", "ordering": ["business_name"]},
        ),
        migrations.CreateModel(
            name="Complex",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="nombre")),
                ("address", models.CharField(blank=True, max_length=240, verbose_name="dirección")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="localidad")),
                ("province", models.CharField(blank=True, max_length=120, verbose_name="provincia")),
                ("notes", models.TextField(blank=True, verbose_name="notas")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="complexes", to="core.businessaccount")),
            ],
            options={"verbose_name": "complejo", "verbose_name_plural": "complejos", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Accommodation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="nombre de la unidad")),
                ("kind", models.CharField(choices=[("CABIN", "Cabaña"), ("APARTMENT", "Departamento"), ("HOUSE", "Casa"), ("OTHER", "Otro")], default="CABIN", max_length=16, verbose_name="tipo")),
                ("capacity", models.PositiveSmallIntegerField(default=2, verbose_name="capacidad máxima")),
                ("bedrooms", models.PositiveSmallIntegerField(default=0, verbose_name="dormitorios")),
                ("beds", models.PositiveSmallIntegerField(default=0, verbose_name="camas")),
                ("size_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name="superficie (m²)")),
                ("description", models.TextField(blank=True, verbose_name="descripción")),
                ("is_active", models.BooleanField(default=True, verbose_name="activa")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accommodations", to="core.businessaccount")),
                ("complex", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accommodations", to="core.complex", verbose_name="complejo")),
            ],
            options={"verbose_name": "alojamiento", "verbose_name_plural": "alojamientos", "ordering": ["complex__name", "name"]},
        ),
        migrations.AddConstraint(model_name="complex", constraint=models.UniqueConstraint(fields=("account", "name"), name="unique_complex_name_per_account")),
        migrations.AddConstraint(model_name="accommodation", constraint=models.UniqueConstraint(fields=("account", "complex", "name"), name="unique_accommodation_name_per_complex")),
    ]
