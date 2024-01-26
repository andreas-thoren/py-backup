# TODO check that map below is correct
rsync_to_robocopy_map = {
    "-a": "/MIR",  # Archive mode (equivalent to /MIR)
    "-r": "/e",  # Recurse into directories (equivalent to /E)
    "-v": "/v",  # Produce verbose output
    "-n": "/l",  # List only, don't copy (equivalent to /L)
    "--delete": "/purge",  # Delete files on the destination that don't exist in source (equivalent to /PURGE)
    "--dry-run": "/l",  # List only, don't copy (equivalent to /L)
}
