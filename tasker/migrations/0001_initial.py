# Generated by Django 2.2.5 on 2019-10-02 12:37

import autoslug.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='label', unique=True)),
                ('label', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('cloned_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clones', to='tasker.Board')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='label', unique_with=['board'])),
                ('label', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('reserved_until', models.DateTimeField(auto_now_add=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='tasker.Board')),
            ],
        ),
        migrations.CreateModel(
            name='Handling',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor', models.CharField(max_length=30)),
                ('start', models.DateTimeField(blank=True, null=True)),
                ('end', models.DateTimeField(blank=True, null=True)),
                ('success', models.BooleanField()),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='handlings', to='tasker.Task')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField()),
                ('handling', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasker_comments', to='tasker.Handling')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to='attachments/')),
                ('handling', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasker_attachments', to='tasker.Handling')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
