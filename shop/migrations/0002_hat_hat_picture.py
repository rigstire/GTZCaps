# Generated by Django 4.2.23 on 2025-07-13 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hat',
            name='hat_picture',
            field=models.ImageField(blank=True, help_text='Upload an image of the hat', null=True, upload_to='hat_images/'),
        ),
    ]
