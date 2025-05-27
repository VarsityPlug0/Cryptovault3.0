from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_investment_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 