# apache-kafka-backup-and-restore
It will take backup of given topic and store that into either local filesystem or S3.

It will auto resume from same point from where it died for some reason given consumer group name is same before and after crash.

**[In Development]**

## Requirements
* confluent-kafka

# How to Run it
python3 backup.py config.json

Sample Config.json
```
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "POLL_TIME": 5.0,
  "FILESYSTEM_TYPE": "LINUX",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 50
}
```
Run Output
```
$ python3 backup.py config.json
Created Successful Backupfile: /tmp/davinder.test/20204226-104202.tar.gz
Created Successful Backup sha256 file: /tmp/davinder.test/20204226-104202.tar.gz.sha256
Created Successful Backupfile: /tmp/davinder.test/20204226-104203.tar.gz
Created Successful Backup sha256 file: /tmp/davinder.test/20204226-104203.tar.gz.sha256
....
```

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
