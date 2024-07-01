# Generated by Django 4.2.11 on 2024-06-28 23:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0007_category_remove_listing_category_listing_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='categories',
        ),
        migrations.AddField(
            model_name='listing',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='listings', to='auctions.category'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='listings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userlisting',
            name='listing',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='userlistings', to='auctions.listing'),
        ),
        migrations.AlterField(
            model_name='userlisting',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='userlistings', to=settings.AUTH_USER_MODEL),
        ),
    ]
