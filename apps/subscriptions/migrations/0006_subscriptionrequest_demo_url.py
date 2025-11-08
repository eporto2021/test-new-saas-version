# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_subscriptionrequest_request_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionrequest',
            name='demo_url',
            field=models.URLField(blank=True, help_text='Demo link to send to user when request is approved (for demo requests)', max_length=500),
        ),
    ]

