from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_add_investment_end_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ] 