# Generated by Django 5.0.6 on 2024-08-07 14:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_app', '0014_alter_orderitem_price_alter_orderitem_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='نام دسته\u200cبندی')),
            ],
            options={
                'verbose_name': 'دسته\u200cبندی',
                'verbose_name_plural': 'دسته\u200cبندی\u200cها',
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='product_app.category', verbose_name='دسته\u200cبندی اصلی')),
                ('products', models.ManyToManyField(blank=True, related_name='subcategories', to='product_app.product', verbose_name='محصولات')),
            ],
            options={
                'verbose_name': 'زیر دسته\u200cبندی',
                'verbose_name_plural': 'زیر دسته\u200cبندی\u200cها',
            },
        ),
    ]
