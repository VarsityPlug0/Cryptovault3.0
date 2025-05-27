from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_investment_return_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='start_date',
            field=models.DateTimeField(auto_now_add=True, default='2025-05-23 20:47:04'),
            preserve_default=False,
        ),
    ] 