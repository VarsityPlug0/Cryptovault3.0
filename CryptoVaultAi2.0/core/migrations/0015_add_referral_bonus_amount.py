from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_investment_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='bonus_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ] 