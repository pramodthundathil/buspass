# Generated by Django 5.0.6 on 2025-03-16 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_buspass_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='buspass',
            name='payment_order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
