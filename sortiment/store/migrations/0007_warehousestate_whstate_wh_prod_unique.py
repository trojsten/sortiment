# Generated by Django 4.1.5 on 2023-01-31 11:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0006_remove_product_total_price_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="warehousestate",
            constraint=models.UniqueConstraint(
                fields=("warehouse", "product"), name="whstate_wh_prod_unique"
            ),
        ),
    ]
