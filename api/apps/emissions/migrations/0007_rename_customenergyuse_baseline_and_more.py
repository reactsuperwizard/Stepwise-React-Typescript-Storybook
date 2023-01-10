# Generated by Django 4.0.2 on 2022-09-28 08:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wells', '0037_alter_wellplannercompletestep_emp_initiatives_and_more'),
        ('emissions', '0006_customempinitiative_customenergyuse_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CustomEnergyUse',
            new_name='Baseline',
        ),
        migrations.RenameModel(
            old_name='CustomEnergyUsePhase',
            new_name='BaselineInput',
        ),
        migrations.RenameField(
            model_name='baselineinput',
            old_name='energy_use',
            new_name='baseline',
        ),
        migrations.AlterUniqueTogether(
            name='baselineinput',
            unique_together={('baseline', 'season', 'phase', 'mode')},
        ),
    ]
