# Generated by Django 4.2.2 on 2023-07-05 05:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="candle",
            name="turn_to0",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
