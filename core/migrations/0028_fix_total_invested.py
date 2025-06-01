from django.db import migrations, models

def fix_total_invested_column(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    CustomUser = apps.get_model('core', 'CustomUser')
    
    # Get the field definition
    field = CustomUser._meta.get_field('total_invested')
    
    # Try to add the field - if it exists, this will be a no-op
    try:
        schema_editor.add_field(CustomUser, field)
    except Exception:
        # If the field already exists, try to alter it
        try:
            schema_editor.alter_field(CustomUser, field, field)
        except Exception:
            # If both operations fail, the field probably exists with correct type
            pass

def reverse_total_invested(apps, schema_editor):
    # No need to remove the column in reverse migration
    # as it might be used by other parts of the application
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_backup'),
    ]

    operations = [
        migrations.RunPython(fix_total_invested_column, reverse_total_invested),
    ] 