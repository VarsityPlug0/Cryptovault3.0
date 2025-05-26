from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_referral_bonus_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ] 