from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_add_investmenttier_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmenttier',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 