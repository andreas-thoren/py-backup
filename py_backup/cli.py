import argparse
from . import utils

def add_common_arguments(subparser: argparse.ArgumentParser):
    # Common arguments for both sync and backup
    subparser.add_argument('source', help='Source directory')
    subparser.add_argument('destination', help='Destination directory')
    subparser.add_argument('--delete', action='store_true', help='Delete extra files from dest that are not present in source.')
    subparser.add_argument('--dry-run', action='store_true', help='Test run without making any actual changes to see what would happen.')

def sync(args: argparse.Namespace):
    # Assuming utils.sync_function takes source, destination, delete, and dry_run as arguments
    utils.sync(args.source, args.destination, args.delete, args.dry_run)

def backup(args: argparse.Namespace):
    # Assuming utils.backup_function takes source, destination, backup_dir, delete, and dry_run as arguments
    utils.backup(args.source, args.destination, args.backup_dir, args.delete, args.dry_run)

def main():
    parser = argparse.ArgumentParser(description="Sync/Backup CLI tool using argparse.")
    subparsers = parser.add_subparsers(help='Commands')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Trigger sync tasks')
    add_common_arguments(sync_parser)
    sync_parser.set_defaults(func=sync)

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Trigger backup tasks')
    add_common_arguments(backup_parser)
    backup_parser.add_argument('backup_dir', help='Backup directory for storing backups of files about to be overwritten or deleted.')
    backup_parser.set_defaults(func=backup)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()