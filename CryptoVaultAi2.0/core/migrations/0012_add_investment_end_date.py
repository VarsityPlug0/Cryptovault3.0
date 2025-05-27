from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_add_investment_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='end_date',
            field=models.DateTimeField(default='2025-05-23 20:47:45'),
            preserve_default=False,
        ),
    ] 