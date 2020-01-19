# Generated by Django 3.0.2 on 2020-01-19 00:37

from django.db import migrations, models
import django.db.models.deletion


def fill_done(apps, schema_editor):
    Task = apps.get_model('tasker', 'Task')
    for task in Task.objects.annotate(successful_handling=models.Max("handlings__success")).all():
        task.done = (task.successful_handling == 1)
        task.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tasker', '0005_auto_20200118_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='done',
            field=models.BooleanField(default=False, verbose_name='done'),
        ),
        migrations.AlterField(
            model_name='board',
            name='cloned_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clones', to='tasker.Board', verbose_name='cloned from'),
        ),
        migrations.RunPython(fill_done),
    ]
