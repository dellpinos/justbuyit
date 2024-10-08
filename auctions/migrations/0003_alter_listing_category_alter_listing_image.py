# Generated by Django 4.2.11 on 2024-06-24 02:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0002_listing_comment_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='listing',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
    ]
