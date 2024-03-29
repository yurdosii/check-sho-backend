# Generated by Django 3.1.7 on 2021-05-09 10:14

import multiselectfield.db.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0006_campaign_run_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignitem',
            name='type',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[['CHECK_PRICE', 'Check price'], ['CHECK_SALE', 'Check sale']], max_length=50, null=True),
        ),
    ]
