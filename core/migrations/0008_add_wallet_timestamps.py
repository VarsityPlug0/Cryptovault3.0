from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_merge_0006_merge_20250523_2236_0006_merge_user_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='wallet',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 