# Apache Kafka Backup and Restore
**Backup Application**
* It will take backup of given topic and store that into either local filesystem or S3.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* upload to s3 is background process and it depends on `RETRY_UPLOAD_SECONDS`.

**Restore Application**
* it will restore from backup dir into given topic.
* `RETRY_SECONDS` controls when to reread `FILESYSTEM_BACKUP_DIR` for new files.

## Requirements
* confluent-kafka
* boto3

# How to Run Kafka Backup Application
```
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXX
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXX

python3 backup.py backup.json
```

**Local Filesytem Backup.json**
```
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "FILESYSTEM_TYPE": "LINUX",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 50
}
```

**S3 backup.json**
```
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "FILESYSTEM_TYPE": "S3",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 50,
  "RETRY_UPLOAD_SECONDS": 100
}
```

**Example S3 Backup Run Output**
```
$ python3 backup.py backup.json
{ "@timestamp": "2020-06-01 10:37:00,168","level": "INFO","thread": "MainThread","name": "root","message": "Successful loading of config.json file" }
{ "@timestamp": "2020-06-01 10:37:00,169","level": "INFO","thread": "MainThread","name": "root","message": "all required variables are successfully" }
{ "@timestamp": "2020-06-01 10:37:00,187","level": "INFO","thread": "Kafka Consumer","name": "root","message": "starting polling on davinder.test" }
{ "@timestamp": "2020-06-01 10:38:17,291","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103817.tar.gz" }
{ "@timestamp": "2020-06-01 10:39:00,631","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103817.tar.gz" }
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
└── current.bin

0 directories, 5 files
```

# How to Run Kafka Restore Application
```
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXX
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXX

python3 restore.py restore.json
```

**Local Filesytem Restore.json**
```
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "RESTORE_TOPIC_NAME": "davinder-restore.test",
  "FILESYSTEM_TYPE": "LINUX",
  "FILESYSTEM_BACKUP_DIR": "/tmp/davinder.test",
  "RETRY_SECONDS": 100
}
```

**Example Local Restore Run Output**
```
$ python3 restore.py restore.json
{ "@timestamp": "2020-06-06 11:33:42,818","level": "INFO","thread": "MainThread","name": "root","message": "loading restore.json file" }
{ "@timestamp": "2020-06-06 11:33:42,819","level": "INFO","thread": "MainThread","name": "root","message": "successful loading of all variables" }
{ "@timestamp": "2020-06-06 11:33:42,823","level": "INFO","thread": "Kafka Producer","name": "root","message": "waiting for more files in /tmp/davinder.test" }
{ "@timestamp": "2020-06-06 11:33:43,822","level": "INFO","thread": "Kafka Producer","name": "root","message": "restore successful of file /tmp/davinder.test/20200606-121934.tar.gz" }}
....
```