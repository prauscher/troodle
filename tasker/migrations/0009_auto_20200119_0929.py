# Generated by Django 3.0.2 on 2020-01-19 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasker', '0008_board_admin_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='board',
            name='admin_id',
            field=models.CharField(help_text='id used to authenticate for admin interface', max_length=30, unique=True, verbose_name='admin id'),
        ),
    ]
