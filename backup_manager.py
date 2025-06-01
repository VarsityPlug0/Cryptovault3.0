import os
import shutil
import datetime
import subprocess
from pathlib import Path
import logging
from django.conf import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class BackupManager:
    def __init__(self):
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.retention_days = 7

    def create_backup(self):
        """Create a backup of the database and media files"""
        try:
            # Create timestamp for backup
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'backup_{timestamp}'
            backup_path.mkdir(exist_ok=True)

            # Backup database
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                db_path = settings.DATABASES['default']['NAME']
                shutil.copy2(db_path, backup_path / 'db.sqlite3')
            else:
                # For PostgreSQL, use pg_dump
                db_url = settings.DATABASES['default']
                dump_file = backup_path / 'database.sql'
                subprocess.run([
                    'pg_dump',
                    f"--host={db_url['HOST']}",
                    f"--port={db_url['PORT']}",
                    f"--username={db_url['USER']}",
                    f"--dbname={db_url['NAME']}",
                    f"--file={dump_file}"
                ], check=True)

            # Backup media files
            media_backup_path = backup_path / 'media'
            if os.path.exists(settings.MEDIA_ROOT):
                shutil.copytree(settings.MEDIA_ROOT, media_backup_path)

            # Create a zip archive
            shutil.make_archive(str(backup_path), 'zip', backup_path)
            shutil.rmtree(backup_path)  # Remove the unzipped backup

            logging.info(f"Backup created successfully: {backup_path}.zip")
            return True

        except Exception as e:
            logging.error(f"Backup failed: {str(e)}")
            return False

    def cleanup_old_backups(self):
        """Remove backups older than retention_days"""
        try:
            current_time = datetime.datetime.now()
            for backup_file in self.backup_dir.glob('backup_*.zip'):
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                age_days = (current_time - file_time).days
                
                if age_days > self.retention_days:
                    backup_file.unlink()
                    logging.info(f"Removed old backup: {backup_file}")

            return True
        except Exception as e:
            logging.error(f"Cleanup failed: {str(e)}")
            return False

    def restore_backup(self, backup_file):
        """Restore from a backup file"""
        try:
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")

            # Create temporary directory for extraction
            temp_dir = self.backup_dir / 'temp_restore'
            temp_dir.mkdir(exist_ok=True)

            # Extract backup
            shutil.unpack_archive(str(backup_path), str(temp_dir), 'zip')

            # Restore database
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                db_backup = temp_dir / 'db.sqlite3'
                if db_backup.exists():
                    shutil.copy2(db_backup, settings.DATABASES['default']['NAME'])
            else:
                # For PostgreSQL, use psql
                db_url = settings.DATABASES['default']
                dump_file = temp_dir / 'database.sql'
                if dump_file.exists():
                    subprocess.run([
                        'psql',
                        f"--host={db_url['HOST']}",
                        f"--port={db_url['PORT']}",
                        f"--username={db_url['USER']}",
                        f"--dbname={db_url['NAME']}",
                        f"--file={dump_file}"
                    ], check=True)

            # Restore media files
            media_backup = temp_dir / 'media'
            if media_backup.exists():
                if os.path.exists(settings.MEDIA_ROOT):
                    shutil.rmtree(settings.MEDIA_ROOT)
                shutil.copytree(media_backup, settings.MEDIA_ROOT)

            # Cleanup
            shutil.rmtree(temp_dir)
            logging.info(f"Backup restored successfully from: {backup_file}")
            return True

        except Exception as e:
            logging.error(f"Restore failed: {str(e)}")
            return False

def create_backup():
    """Function to be called from Django management command"""
    manager = BackupManager()
    if manager.create_backup():
        manager.cleanup_old_backups()
        return True
    return False

def restore_backup(backup_file):
    """Function to be called from Django management command"""
    manager = BackupManager()
    return manager.restore_backup(backup_file) 