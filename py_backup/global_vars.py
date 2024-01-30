# These options are the default options for the different backup functions
# used by folder_backup function in core.py
# These can be modified if another default behaviour is wished for but do not
# add options for --delete, --backup and --backup-dir since these are already
# handled by get_rsync_defaults
default_options = {
    "rsync": ["-a", "-i", "-v", "-h"],
    "robocopy": ["/E", "/DCOPY:DAT", "/COPY:DAT", "/R:3", "/W:1"],
}
