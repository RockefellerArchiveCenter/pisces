# Generated by Django 2.2.6 on 2020-02-01 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fetcher', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fetchrun',
            name='source',
            field=models.CharField(choices=[(0, 'ArchivesSpace'), (1, 'Cartographer')], max_length=100),
        ),
    ]
