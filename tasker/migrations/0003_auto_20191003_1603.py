# Generated by Django 2.2.5 on 2019-10-03 16:03

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tasker', '0002_auto_20191003_1446'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='handling',
            name='unique_handling',
        ),
        migrations.AlterField(
            model_name='handling',
            name='start',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='task',
            name='reserved_until',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddConstraint(
            model_name='handling',
            constraint=models.UniqueConstraint(fields=('task', 'editor', 'start'), name='unique_start'),
        ),
        migrations.AddConstraint(
            model_name='handling',
            constraint=models.UniqueConstraint(fields=('task', 'editor', 'end'), name='unique_end'),
        ),
    ]