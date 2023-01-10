# Generated by Django 4.0.2 on 2022-10-10 12:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0008_auto_20220324_1446'),
        ('emissions', '0013_customvessel'),
    ]

    operations = [
        migrations.AddField(
            model_name='customvessel',
            name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='tenants.tenant'),
        ),
    ]
