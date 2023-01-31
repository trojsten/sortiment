# Generated by Django 4.1.5 on 2023-01-31 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0004_alter_product_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="warehouse",
            name="ip",
            field=models.GenericIPAddressField(default="10.0.0.1", unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="product",
            name="barcode",
            field=models.CharField(max_length=32, unique=True),
        ),
    ]