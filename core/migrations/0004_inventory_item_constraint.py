from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0003_finance_inventory")]
    operations = [
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.UniqueConstraint(fields=("accommodation", "name"), name="unique_inventory_item_per_accommodation"),
        ),
    ]
