# Effective commands for rsync and robocopy to use with the scripts

## rsync
Add -n for dryrun!!  

#### Command 1. Supervised sync operation
```rsync -aivh --delete /mnt/samsung870/share1/OneDrive/ /mnt/QNAPMain/OneDrive/```  
- ivh flags are related to how information is showed. i = itemize-changes. v = verbose, together with i adds header and footer with extra info. -h human readable numbers.

#### Command 2. Unsupervised from login shell.
```nohup rsync -aivh --delete /mnt/samsung870/share1/OneDrive/ /mnt/QNAPMain/OneDrive/ > ~/rsync_log.txt 2>&1 &```
- nohup:  If rsync is run from login shell and process should not be terminated upon login out.  
- Redirect output to log file  
- 2>&1 means append error output to standard output
- & run process in background

## robocopy