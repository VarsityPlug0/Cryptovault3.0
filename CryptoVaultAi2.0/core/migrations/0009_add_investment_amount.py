from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_wallet_timestamps'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='amount',
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0),
            preserve_default=False,
        ),
    ] 