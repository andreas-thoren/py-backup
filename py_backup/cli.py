import argparse
from .comparer import DirComparator
from . import utils


def valid_num_incremental(value: str) -> int:
    try:
        ivalue = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer!") from exc

    if ivalue < 2 or ivalue > 100:
        raise argparse.ArgumentTypeError(
            "--num-incremental needs to in the range 2-100!"
        )

    return ivalue


def add_common_arguments(subparser: argparse.ArgumentParser):
    subparser.add_argument("source", help="Source directory")
    subparser.add_argument("destination", help="Destination directory")
    subparser.add_argument(
        "-n",
        "--dry-run",
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


def compare(args: argparse.Namespace):
    excludes = args.exclude if args.exclude else None
    comparer = DirComparator(args.dir1, args.dir2, args.dir1_name, args.dir2_name)
    comparer.follow_symlinks = args.follow_symlinks
    comparer.compare_directories(
        unilateral_compare=args.unilateral_compare,
        include_equal_entries=args.include_equals,
        excludes=excludes,
    )

    if args.expand_dirs:
        comparer.expand_dirs(excludes)

    print(comparer.get_comparison_result())


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
        "-b",
        "--backup-dir",
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
        "-b",
        "--backup-dir",
        default="",
        help="Backup directory for storing backups of files about to be overwritten/deleted.",
    )
    backup_parser.set_defaults(func=backup)

    # Incremental backup command
    msg_incremental = (
        "Mirrors source directory to destination directory but incrementally "
        + "backups overwritten/deleted files:"
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
        "-b",
        "--backup-dir",
        required=True,
        help="Backup directory for storing backups of files about to be overwritten/deleted.",
    )

    incremental_parser.add_argument(
        "-num",
        "--num-incremental",
        required=True,
        type=valid_num_incremental,
        help="Number of incremental backups to keep",
    )
    incremental_parser.set_defaults(func=incremental)

    # Compare directory command. Does not do any backups!
    msg_compare = (
        "Compares 2 directories. Creates nicely formated output of differences!"
    )
    compare_parser = subparsers.add_parser("compare", description=msg_compare)

    compare_parser.add_argument("dir1", help="First directory of comparison!")
    compare_parser.add_argument("dir2", help="Second directory of comparison!")
    compare_parser.add_argument(
        "-u",
        "--unilateral-compare",
        action="store_true",
        help=(
            "If set only compares dir1 with dir2 but not the other way around. "
            + "This means that exlusive dir2 items will not be included in result."
        ),
    )
    compare_parser.add_argument(
        "-s",
        "--follow-symlinks",
        action="store_true",
        help=("Treats symlinks as the file/dir they point to."),
    )
    compare_parser.add_argument(
        "-i",
        "--include-equals",
        action="store_true",
        help=("Include equal files in the comparison result"),
    )
    compare_parser.add_argument(
        "--expand-dirs",
        action="store_true",
        help=(
            "Expand unique dirs so that all nested files/dirs within gets added to the result"
        ),
    )
    compare_parser.add_argument(
        "--dir1-name",
        default="dir1",
        help="What dir1 will be called in the result. If not used dir1_name defaults to 'dir1'",
    )
    compare_parser.add_argument(
        "--dir2-name",
        default="dir2",
        help="What dir2 will be called in the result. If not used dir2_name defaults to 'dir2'",
    )
    compare_parser.add_argument(
        "--exclude",
        nargs="*",
        help="List of exclude patterns (Unix style). Files or directories matching these patterns will be excluded from comparison.",
        default=[],
    )
    compare_parser.set_defaults(func=compare)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
