# Generated by Django 4.1.5 on 2023-01-30 16:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_alter_sortimentuser_barcode_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sortimentuser",
            name="credit",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
    ]
