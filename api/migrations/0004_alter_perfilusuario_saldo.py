# Generated by Django 5.2 on 2025-04-17 01:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_perfilusuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfilusuario',
            name='saldo',
            field=models.DecimalField(decimal_places=2, default=500000, max_digits=12),
        ),
    ]
