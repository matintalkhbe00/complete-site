# Generated by Django 5.0.6 on 2024-08-14 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_app', '0009_alter_user_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='postal_code',
            field=models.CharField(max_length=50),
        ),
    ]
