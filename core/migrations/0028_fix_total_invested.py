from django.db import migrations

def check_total_invested_exists(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    CustomUser = apps.get_model('core', 'CustomUser')
    
    # Check if the column exists
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='core_customuser' 
            AND column_name='total_invested';
        """)
        exists = cursor.fetchone() is not None
        
        if not exists:
            # Add the column if it doesn't exist
            cursor.execute("""
                ALTER TABLE core_customuser 
                ADD COLUMN total_invested DECIMAL(12,2) DEFAULT 0;
            """)

def reverse_total_invested(apps, schema_editor):
    # No need to remove the column in reverse migration
    # as it might be used by other parts of the application
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_backup'),
    ]

    operations = [
        migrations.RunPython(check_total_invested_exists, reverse_total_invested),
    ] 