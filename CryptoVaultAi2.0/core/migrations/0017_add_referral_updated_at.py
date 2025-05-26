from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_referral_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 