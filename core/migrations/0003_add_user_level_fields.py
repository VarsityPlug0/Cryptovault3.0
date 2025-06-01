from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_auto_reinvest'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='level',
            field=models.IntegerField(default=1),
        ),
    ] 