from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    dependencies=[("core","0001_initial"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.AddField(model_name="accommodation",name="base_nightly_rate",field=models.DecimalField(decimal_places=2,default=0,max_digits=12,verbose_name="tarifa base por noche")),
        migrations.AddField(model_name="accommodation",name="base_currency",field=models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],default="ARS",max_length=3,verbose_name="moneda de tarifa")),
        migrations.CreateModel(name="Guest",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("full_name",models.CharField(max_length=180,verbose_name="nombre y apellido")),
            ("phone",models.CharField(blank=True,max_length=40,verbose_name="teléfono")),
            ("email",models.EmailField(blank=True,max_length=254,verbose_name="correo electrónico")),
            ("document_number",models.CharField(blank=True,max_length=50,verbose_name="documento")),
            ("notes",models.TextField(blank=True,verbose_name="notas")),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="guests",to="core.businessaccount")),
        ],options={"ordering":["full_name"]}),
        migrations.CreateModel(name="PriceRule",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(blank=True,max_length=120,verbose_name="nombre de la tarifa")),
            ("guest_count",models.PositiveSmallIntegerField(blank=True,help_text="Dejar vacío para cualquier cantidad.",null=True,verbose_name="cantidad de huéspedes")),
            ("valid_from",models.DateField(blank=True,null=True,verbose_name="desde")),
            ("valid_until",models.DateField(blank=True,null=True,verbose_name="hasta")),
            ("nightly_rate",models.DecimalField(decimal_places=2,max_digits=12,verbose_name="precio por noche")),
            ("currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],default="ARS",max_length=3,verbose_name="moneda")),
            ("minimum_nights",models.PositiveSmallIntegerField(default=1,verbose_name="mínimo de noches")),
            ("is_active",models.BooleanField(default=True,verbose_name="activa")),
            ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="price_rules",to="core.businessaccount")),
            ("accommodation",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="price_rules",to="core.accommodation")),
        ],options={"ordering":["accommodation__name","valid_from","guest_count"],"verbose_name":"regla de precio","verbose_name_plural":"reglas de precios"}),
        migrations.CreateModel(name="Reservation",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("check_in",models.DateField(verbose_name="ingreso")),
            ("check_out",models.DateField(verbose_name="egreso")),
            ("guest_count",models.PositiveSmallIntegerField(verbose_name="huéspedes")),
            ("status",models.CharField(choices=[("PENDING","Pendiente"),("CONFIRMED","Confirmada"),("CHECKED_IN","En estadía"),("COMPLETED","Finalizada"),("CANCELLED","Cancelada")],default="CONFIRMED",max_length=16,verbose_name="estado")),
            ("total_price",models.DecimalField(decimal_places=2,max_digits=12,verbose_name="importe acordado")),
            ("currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],default="ARS",max_length=3,verbose_name="moneda")),
            ("notes",models.TextField(blank=True,verbose_name="notas")),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="reservations",to="core.businessaccount")),
            ("accommodation",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="reservations",to="core.accommodation")),
            ("guest",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="reservations",to="core.guest")),
        ],options={"ordering":["check_in","accommodation__name"]}),
    ]
