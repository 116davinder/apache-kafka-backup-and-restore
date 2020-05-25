# apache-kafka-backup-and-restore
It will take backup of given topic and store that into either local filesystem or S3.

## Requirements
* confluent-kafka

# How to Run it
python3 backup.py

# Backup Directory Structure
```
$ tree davinder.test/
davinder.test/
├── 20204025-154046.tar.gz
├── 20204025-154046.tar.gz.sha256
├── 20204325-154344.tar.gz
├── 20204325-154344.tar.gz.sha256
├── 20204325-154345.tar.gz
├── 20204325-154345.tar.gz.sha256
└── current.bin

0 directories, 7 files
```
