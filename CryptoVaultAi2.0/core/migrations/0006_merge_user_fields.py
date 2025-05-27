from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_merge_0002_add_auto_reinvest_0004_auto_20250523_2230'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='total_invested',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='customuser',
            name='level',
            field=models.IntegerField(default=1),
        ),
    ] 