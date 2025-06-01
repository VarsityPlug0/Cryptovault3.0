from django.core.management.base import BaseCommand, CommandError
from backup_manager import create_backup, restore_backup
import os

class Command(BaseCommand):
    help = 'Manage database and media backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['create', 'restore'],
            required=True,
            help='Action to perform: create or restore backup'
        )
        parser.add_argument(
            '--file',
            help='Backup file to restore (required for restore action)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create':
            self.stdout.write('Creating backup...')
            if create_backup():
                self.stdout.write(self.style.SUCCESS('Backup created successfully'))
            else:
                raise CommandError('Backup creation failed')
                
        elif action == 'restore':
            if not options['file']:
                raise CommandError('--file argument is required for restore action')
                
            self.stdout.write(f'Restoring from backup: {options["file"]}...')
            if restore_backup(options['file']):
                self.stdout.write(self.style.SUCCESS('Backup restored successfully'))
            else:
                raise CommandError('Backup restoration failed') 