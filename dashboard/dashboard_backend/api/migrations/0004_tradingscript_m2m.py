# Generated by Django 5.0.1 on 2024-01-16 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_tradingscript_entry_rate_tradingscript_net_quantity_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tradingscript",
            name="m2m",
            field=models.IntegerField(default=0),
        ),
    ]
