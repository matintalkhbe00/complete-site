# Generated by Django 5.0.6 on 2024-08-10 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_app', '0007_alter_address_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, default='img/static/default-profile.jpg', null=True, upload_to='profile_pictures/', verbose_name='عکس پروفایل'),
        ),
    ]
