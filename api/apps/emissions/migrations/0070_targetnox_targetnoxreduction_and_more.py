# Generated by Django 4.0.2 on 2022-12-23 13:02

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wells', '0070_merge_20221207_0923'),
        ('emissions', '0069_merge_20221220_1343'),
    ]

    operations = [
        migrations.CreateModel(
            name='TargetNOX',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('asset', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('boilers', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('vessels', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('helicopters', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('external_energy_supply', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
                'verbose_name': 'Target NOX',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TargetNOXReduction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                (
                    'emission_reduction_initiative',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to='emissions.emissionreductioninitiative'
                    ),
                ),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='emissions.targetnox')),
            ],
            options={
                'verbose_name': 'Target NOX reduction',
                'unique_together': {('target', 'emission_reduction_initiative')},
            },
        ),
        migrations.AddField(
            model_name='targetnox',
            name='emission_reduction_initiatives',
            field=models.ManyToManyField(
                through='emissions.TargetNOXReduction', to='emissions.EmissionReductionInitiative'
            ),
        ),
        migrations.AddField(
            model_name='targetnox',
            name='planned_step',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wells.wellplannerplannedstep'),
        ),
        migrations.AlterUniqueTogether(
            name='targetnox',
            unique_together={('planned_step', 'datetime')},
        ),
        migrations.CreateModel(
            name='BaselineNOX',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('asset', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('boilers', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('vessels', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('helicopters', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('external_energy_supply', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                (
                    'planned_step',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wells.wellplannerplannedstep'),
                ),
            ],
            options={
                'verbose_name': 'Baseline NOX',
                'abstract': False,
                'unique_together': {('planned_step', 'datetime')},
            },
        ),
    ]
