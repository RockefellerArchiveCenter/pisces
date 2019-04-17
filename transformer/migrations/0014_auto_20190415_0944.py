# Generated by Django 2.0.13 on 2019-04-15 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0013_auto_20190413_0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='transformrun',
            name='source',
            field=models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Pisces'), (5, 'Cartographer')], default=3, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sourcedata',
            name='source',
            field=models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Cartographer')], max_length=100),
        ),
    ]