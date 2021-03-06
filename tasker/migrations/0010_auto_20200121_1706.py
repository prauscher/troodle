# Generated by Django 3.0.2 on 2020-01-21 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasker', '0009_auto_20200119_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='requires',
            field=models.ManyToManyField(blank=True, help_text='Tasks which have to be done before this task can be started.', related_name='required_by', to='tasker.Task', verbose_name='requires'),
        ),
    ]
