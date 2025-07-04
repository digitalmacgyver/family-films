# Generated by Django 5.2.4 on 2025-07-03 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='thumbnail_high_url',
            field=models.URLField(blank=True, help_text='High quality thumbnail (hqdefault)'),
        ),
        migrations.AddField(
            model_name='film',
            name='thumbnail_medium_url',
            field=models.URLField(blank=True, help_text='Medium quality thumbnail (mqdefault)'),
        ),
        migrations.AlterField(
            model_name='film',
            name='thumbnail_url',
            field=models.URLField(help_text='YouTube thumbnail URL (maxresdefault)'),
        ),
    ]
