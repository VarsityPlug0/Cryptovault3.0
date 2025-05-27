from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_add_investment_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='return_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
            preserve_default=False,
        ),
    ] 