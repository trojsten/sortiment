# Generated by Django 4.1.5 on 2023-03-06 19:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_alter_sortimentuser_barcode_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="creditlog",
            name="message",
            field=models.CharField(default="", max_length=128),
        ),
    ]
