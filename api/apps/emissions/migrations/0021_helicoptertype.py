# Generated by Django 4.0.2 on 2022-10-13 13:11

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0008_auto_20220324_1446'),
        ('emissions', '0020_vesseltype_deleted'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='HelicopterType',
                    fields=[
                        (
                            'id',
                            models.BigAutoField(
                                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                            ),
                        ),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('name', models.CharField(blank=True, max_length=255)),
                        (
                            'fuel',
                            models.FloatField(
                                help_text='Fuel consumption (Litres/h)',
                                validators=[django.core.validators.MinValueValidator(0)],
                            ),
                        ),
                        (
                            'fuel_cost',
                            models.FloatField(
                                help_text='Fuel cost (USD/mT)', validators=[django.core.validators.MinValueValidator(0)]
                            ),
                        ),
                        (
                            'nox',
                            models.FloatField(
                                help_text='NOX p/mT fuel (Kg)', validators=[django.core.validators.MinValueValidator(0)]
                            ),
                        ),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tenants.tenant')),
                    ],
                    options={
                        'abstract': False,
                    },
                )
            ]
        )
    ]
