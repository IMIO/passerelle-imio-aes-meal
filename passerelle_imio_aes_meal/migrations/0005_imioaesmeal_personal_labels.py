# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-29 11:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passerelle_imio_aes_meal', '0004_auto_20190729_1311'),
    ]

    operations = [
        migrations.AddField(
            model_name='imioaesmeal',
            name='personal_labels',
            field=models.TextField(blank=True, default=b'{}', help_text=b'Personal labels: define like a dictionary : {"fruit":"new label fruit","repas":"repas chaud",...}', verbose_name=b'Personalize labels'),
        ),
    ]
