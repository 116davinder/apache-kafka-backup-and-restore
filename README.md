# Apache Kafka Backup and Restore
**Backup Application**
* It will take backup of given topic and store that into either local filesystem or S3.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* `RETRY_UPLOAD_SECONDS` controls upload to s3 or other cloud storage.
* `NUMBER_OF_KAFKA_THREADS` is used to parallelise reading from kafka topic.
It should not be more than number of partitions.
* `LOG_LEVEL` values can be found https://docs.python.org/3/library/logging.html#logging-levels
* `NUMBER_OF_MESSAGE_PER_BACKUP_FILE` will try to keep this number consistent in file
but if application got restarted then it may be vary for first back file.

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
  "BOOTSTRAP_SERVERS": "kafka01:9092,kafka02:9092,kafka03:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "FILESYSTEM_TYPE": "LINUX",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 1000,
  "RETRY_UPLOAD_SECONDS": 100,
  "NUMBER_OF_KAFKA_THREADS": 2,
  "LOG_LEVEL": 20
}
```

**S3 backup.json**
```
{
  "BOOTSTRAP_SERVERS": "kafka01:9092,kafka02:9092,kafka03:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "FILESYSTEM_TYPE": "S3",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 1000,
  "RETRY_UPLOAD_SECONDS": 100,
  "NUMBER_OF_KAFKA_THREADS": 2,
  "LOG_LEVEL": 20
}
```
**Example Local Backup Run Output**
```
{ "@timestamp": "2020-06-08 10:56:34,557","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-08 10:56:34,557","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-08 10:56:34,557","level": "INFO","thread": "Kafka Consumer 2","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-08 10:56:51,590","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/1/20200608-105651.tar.gz" }
{ "@timestamp": "2020-06-08 10:56:51,593","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/1/20200608-105651.tar.gz.sha256" }
{ "@timestamp": "2020-06-08 10:57:17,270","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/0/20200608-105717.tar.gz" }
{ "@timestamp": "2020-06-08 10:57:17,277","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/0/20200608-105717.tar.gz.sha256" }
{ "@timestamp": "2020-06-08 10:57:17,399","level": "INFO","thread": "Kafka Consumer 2","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/2/20200608-105717.tar.gz" }
{ "@timestamp": "2020-06-08 10:57:17,406","level": "INFO","thread": "Kafka Consumer 2","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/2/20200608-105717.tar.gz.sha256" }
...
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
/tmp/davinder.test/
├── 0
│   ├── 20200608-102909.tar.gz
│   ├── 20200608-102909.tar.gz.sha256
│   └── current.bin
├── 1
│   ├── 20200608-102909.tar.gz
│   ├── 20200608-102909.tar.gz.sha256
│   └── current.bin
└── 2
    ├── 20200608-102909.tar.gz
    ├── 20200608-102909.tar.gz.sha256
    └── current.bin

3 directories, 9 files
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