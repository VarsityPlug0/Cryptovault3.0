from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_add_investmenttier_min_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmenttier',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ] 