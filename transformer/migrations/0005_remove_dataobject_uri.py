# Generated by Django 2.2.10 on 2020-06-24 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0004_auto_20200624_1702'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataobject',
            name='uri',
        ),
    ]
