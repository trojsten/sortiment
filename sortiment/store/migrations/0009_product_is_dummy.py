# Generated by Django 4.1.5 on 2023-01-31 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0008_alter_warehousestate_total_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_dummy",
            field=models.BooleanField(default=False),
        ),
    ]
