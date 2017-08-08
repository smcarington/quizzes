# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-08 21:13
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import quizzes.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('open_enrollment', models.BooleanField(default=False)),
                ('status', models.BooleanField(default=False)),
            ],
            options={
                'permissions': (('can_edit_quiz', 'Can edit the quiz'),),
            },
        ),
        migrations.CreateModel(
            name='CSVFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_file', models.FileField(upload_to='tmp/')),
            ],
        ),
        migrations.CreateModel(
            name='MarkedQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.IntegerField(default=1, verbose_name='Category')),
                ('problem_str', models.TextField(verbose_name='Problem')),
                ('choices', models.TextField(null=True, verbose_name='Choices')),
                ('num_vars', models.IntegerField(null=True)),
                ('answer', models.TextField(verbose_name='Answer')),
                ('functions', models.TextField(default='{}', verbose_name='Functions')),
                ('q_type', models.CharField(choices=[('D', 'Direct Entry'), ('MC', 'Multiple Choice'), ('TF', 'True/False')], default='D', max_length=2, verbose_name='Question Type')),
                ('mc_choices', models.TextField(blank=True, default='[]', verbose_name='Multiple Choice')),
            ],
            options={
                'verbose_name': 'Marked Question',
                'ordering': ['quiz', 'category'],
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('tries', models.IntegerField(default=0, verbose_name='Tries')),
                ('live', models.DateTimeField(verbose_name='Live on')),
                ('expires', models.DateTimeField(verbose_name='Expires on')),
                ('out_of', models.IntegerField(default=1, verbose_name='Points')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
            },
        ),
        migrations.CreateModel(
            name='StudentQuizResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt', models.IntegerField(default=1, null=True)),
                ('cur_quest', models.IntegerField(default=1, null=True)),
                ('result', models.TextField(default='{}')),
                ('score', models.IntegerField(null=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizzes.Quiz')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quiz Result',
            },
        ),
        migrations.CreateModel(
            name='UserMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('courses', models.ManyToManyField(to='quizzes.Course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='markedquestion',
            name='quiz',
            field=models.ForeignKey(null=True, on_delete=quizzes.models.Quiz, to='quizzes.Quiz'),
        ),
    ]
