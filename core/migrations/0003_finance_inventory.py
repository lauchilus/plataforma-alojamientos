from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
 dependencies=[("core","0002_reservations_and_pricing")]
 operations=[
  migrations.CreateModel(name="Expense",fields=[
   ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
   ("category",models.CharField(max_length=100,verbose_name="categoría")),("detail",models.CharField(max_length=240,verbose_name="detalle")),
   ("spent_on",models.DateField(verbose_name="fecha")),("amount",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="importe")),
   ("currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],max_length=3,verbose_name="moneda")),
   ("base_amount",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="equivalente en moneda de referencia")),
   ("base_currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],max_length=3)),
   ("exchange_rate",models.DecimalField(decimal_places=8,default=1,max_digits=18,verbose_name="tasa aplicada")),("quote_date",models.DateField(blank=True,null=True,verbose_name="fecha de cotización")),
   ("quote_source",models.CharField(blank=True,max_length=120,verbose_name="fuente")),("created_at",models.DateTimeField(auto_now_add=True)),
   ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="expenses",to="core.businessaccount")),
   ("accommodation",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="expenses",to="core.accommodation",verbose_name="alojamiento (opcional)")),
  ],options={"ordering":["-spent_on","-id"]}),
  migrations.CreateModel(name="InventoryItem",fields=[
   ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
   ("name",models.CharField(max_length=140,verbose_name="elemento")),("category",models.CharField(blank=True,max_length=80,verbose_name="categoría")),
   ("unit_label",models.CharField(default="unidad",max_length=30,verbose_name="unidad")),("track_per_stay",models.BooleanField(default=False,verbose_name="registrar entregas y devoluciones por estadía")),
   ("clean_quantity",models.PositiveIntegerField(default=0,verbose_name="limpias / disponibles")),("in_use_quantity",models.PositiveIntegerField(default=0,verbose_name="entregadas / en uso")),
   ("used_quantity",models.PositiveIntegerField(default=0,verbose_name="usadas / por limpiar")),("damaged_quantity",models.PositiveIntegerField(default=0,verbose_name="dañadas")),
   ("missing_quantity",models.PositiveIntegerField(default=0,verbose_name="faltantes")),("is_active",models.BooleanField(default=True,verbose_name="activo")),
   ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="inventory_items",to="core.businessaccount")),
   ("accommodation",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="inventory_items",to="core.accommodation")),
  ],options={"ordering":["accommodation__name","name"]}),
  migrations.CreateModel(name="Payment",fields=[
   ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
   ("amount",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="importe recibido")),("currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],max_length=3,verbose_name="moneda recibida")),
   ("method",models.CharField(choices=[("CASH","Efectivo"),("TRANSFER","Transferencia"),("CARD","Tarjeta"),("MERCADO_PAGO","Mercado Pago"),("OTHER","Otro")],default="TRANSFER",max_length=20,verbose_name="medio de pago")),
   ("paid_on",models.DateField(verbose_name="fecha de cobro")),("reservation_amount",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="equivalente en moneda de reserva")),
   ("reservation_currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],max_length=3)),
   ("base_amount",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="equivalente en moneda de referencia")),
   ("base_currency",models.CharField(choices=[("ARS","Peso argentino"),("USD","Dólar estadounidense"),("EUR","Euro"),("BRL","Real brasileño"),("CLP","Peso chileno"),("UYU","Peso uruguayo")],max_length=3)),
   ("exchange_rate",models.DecimalField(decimal_places=8,default=1,max_digits=18,verbose_name="tasa aplicada")),("quote_date",models.DateField(blank=True,null=True,verbose_name="fecha de cotización")),
   ("quote_source",models.CharField(blank=True,max_length=120,verbose_name="fuente")),("reference",models.CharField(blank=True,max_length=160,verbose_name="referencia")),
   ("created_at",models.DateTimeField(auto_now_add=True)),("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="payments",to="core.businessaccount")),
   ("reservation",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="payments",to="core.reservation")),
  ],options={"ordering":["-paid_on","-id"]}),
  migrations.CreateModel(name="InventoryMovement",fields=[
   ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
   ("movement_type",models.CharField(choices=[("DELIVER_CLEAN","Entrega limpia"),("REPLACEMENT","Reposición limpia"),("RETURN_USED","Retiro de usada"),("LAUNDRY_CLEAN","Regreso limpia"),("DAMAGE","Marcar dañada"),("MISSING","Marcar faltante"),("STOCK_IN","Ingreso de stock")],max_length=20,verbose_name="movimiento")),
   ("quantity",models.PositiveIntegerField(verbose_name="cantidad")),("source_state",models.CharField(blank=True,choices=[("clean","limpia/disponible"),("in_use","entregada/en uso"),("used","usada/por limpiar")],max_length=12,verbose_name="estado de origen")),
   ("notes",models.CharField(blank=True,max_length=240,verbose_name="nota")),("created_at",models.DateTimeField(auto_now_add=True)),
   ("account",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="inventory_movements",to="core.businessaccount")),
   ("item",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="movements",to="core.inventoryitem")),
   ("reservation",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="inventory_movements",to="core.reservation")),
  ],options={"ordering":["-created_at"]}),
  migrations.CreateModel(name="ExpenseAllocation",fields=[
   ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
   ("amount_base",models.DecimalField(decimal_places=2,max_digits=14,verbose_name="importe asignado")),("created_at",models.DateTimeField(auto_now_add=True)),
   ("accommodation",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="expense_allocations",to="core.accommodation")),
   ("expense",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="allocations",to="core.expense")),
  ]),
  migrations.AddConstraint(model_name="expenseallocation",constraint=models.UniqueConstraint(fields=("expense","accommodation"),name="unique_expense_allocation_per_accommodation")),
 ]
