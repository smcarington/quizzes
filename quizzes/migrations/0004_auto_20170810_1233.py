# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-10 16:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_auto_20170810_1224'),
    ]

    operations = [
        migrations.RenameField(
            model_name='markedquestion',
            old_name='_problem_str',
            new_name='problem_str',
        ),
    ]
