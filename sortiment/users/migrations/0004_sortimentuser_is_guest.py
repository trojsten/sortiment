# Generated by Django 4.1.5 on 2023-01-31 15:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_alter_sortimentuser_credit"),
    ]

    operations = [
        migrations.AddField(
            model_name="sortimentuser",
            name="is_guest",
            field=models.BooleanField(default=False),
        ),
    ]
