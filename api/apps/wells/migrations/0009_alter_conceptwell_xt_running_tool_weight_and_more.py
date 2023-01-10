# Generated by Django 4.0.2 on 2022-05-05 12:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wells', '0008_auto_20220505_0920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conceptwell',
            name='xt_running_tool_weight',
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(200)],
                verbose_name='XT running tool weight (t)',
            ),
        ),
        migrations.AlterField(
            model_name='customwell',
            name='xt_running_tool_weight',
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(200)],
                verbose_name='XT running tool weight (t)',
            ),
        ),
    ]