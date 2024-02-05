import argparse
from . import utils


def add_common_arguments(subparser: argparse.ArgumentParser):
    subparser.add_argument("source", help="Source directory")
    subparser.add_argument("destination", help="Destination directory")
    subparser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Test run without making any actual changes to see what would happen.",
    )


def mirror(args: argparse.Namespace):
    utils.mirror(args.source, args.destination, args.dry_run, args.backup_dir)


def backup(args: argparse.Namespace):
    utils.backup(args.source, args.destination, args.dry_run, args.backup_dir)


def incremental(args: argparse.Namespace):
    utils.incremental(
        args.source,
        args.destination,
        args.dry_run,
        args.backup_dir,
        args.num_incremental,
    )


def main():
    parser = argparse.ArgumentParser(description="Sync/Backup CLI tool using argparse.")
    subparsers = parser.add_subparsers(help="Commands", dest="cmd", required=True)

    # mirror command
    msg_mirror = (
        "Mirrors source directory to destination directory:"
        + "\n- Deletes files in destination directory which doesn't exist in source!"
        + "\n- Overwrites files in destination with files from source if modification times differ!"
        + "\n- Tries to preserve file/directory time stamps and attributes"
    )

    mirror_parser = subparsers.add_parser(
        "mirror",
        description=msg_mirror,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_arguments(mirror_parser)
    mirror_parser.add_argument(
        "-b", "--backup-dir",
        default="",
        help="Backup directory for storing backups of files about to be overwritten/deleted.",
    )
    mirror_parser.set_defaults(func=mirror)

    # Backup command
    msg_backup = (
        "Backups files and directories in source recursively into destination:"
        + "\n- Does not delete files in destination which doesn't exist in source"
        + "\n- Overwrites files in destination with files from source if modification times differ!"
        + "\n- Tries to preserve file/directory time stamps and attributes"
    )

    backup_parser = subparsers.add_parser(
        "backup",
        description=msg_backup,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_arguments(backup_parser)
    backup_parser.add_argument(
        "-b", "--backup-dir",
        default="",
        help="Backup directory for storing backups of files about to be overwritten/deleted.",
    )
    backup_parser.set_defaults(func=backup)

    # Incremental backup command
    msg_incremental = (
        "Mirrors source directory to destination directory:"
        + "\n- Backs up deleted and overwritten files to specified backup directory!"
        + "\n- Files/dirs backed up this way will be placed in nested subdirectories"
        + "\n- num_incremental specifies how many of these nested subdirectories will be kept before being deleted."
        + "\n- Deletes files in destination directory which doesn't exist in source!"
        + "\n- Overwrites files in destination with files from source if modification times differ!"
        + "\n- Tries to preserve file/directory time stamps and attributes"
    )

    incremental_parser = subparsers.add_parser(
        "incremental",
        description=msg_incremental,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_arguments(incremental_parser)

    incremental_parser.add_argument(
        "-b", "--backup-dir",
        required=True,
        help="Backup directory for storing backups of files about to be overwritten/deleted.",
    )

    incremental_parser.add_argument(
        "-num", "--num-incremental",
        required=True,
        type=int,
        help="Number of incremental backups to keep",
    )
    incremental_parser.set_defaults(func=incremental)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
