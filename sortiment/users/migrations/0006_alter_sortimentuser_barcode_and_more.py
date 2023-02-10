# Generated by Django 4.1.5 on 2023-02-10 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_creditlog_is_purchase"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sortimentuser",
            name="barcode",
            field=models.CharField(
                blank=True, max_length=32, verbose_name="čiarový kód"
            ),
        ),
        migrations.AlterField(
            model_name="sortimentuser",
            name="credit",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=6, verbose_name="kredit"
            ),
        ),
        migrations.AlterField(
            model_name="sortimentuser",
            name="first_name",
            field=models.CharField(max_length=150, verbose_name="meno"),
        ),
        migrations.AlterField(
            model_name="sortimentuser",
            name="last_name",
            field=models.CharField(max_length=150, verbose_name="priezvisko"),
        ),
        migrations.AlterField(
            model_name="sortimentuser",
            name="password",
            field=models.CharField(blank=True, max_length=128, verbose_name="heslo"),
        ),
    ]
