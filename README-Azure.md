# Apache Kafka Backup and Restore on Azure Cloud

**Production Kafka Deployment Using Ansible**
* https://github.com/116davinder/kafka-cluster-ansible/wiki

**General Notes**
* `LOG_LEVEL` values can be found https://docs.python.org/3/library/logging.html#logging-levels
* `If there are too many get/put requests to Azure then increase NUMBER_OF_MESSAGE_PER_BACKUP_FILE to reduce Azure requests.`

## Requirements
* confluent-kafka
* azure-storage-blob

# Kafka Backup Application

* It will take backup of given topic and store that into either local filesystem or S3.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* `RETRY_UPLOAD_SECONDS` controls upload to s3 or other cloud storage.
* `NUMBER_OF_KAFKA_THREADS` is used to parallelise reading from kafka topic.
It should not be more than number of partitions.
* `NUMBER_OF_MESSAGE_PER_BACKUP_FILE` will try to keep this number consistent in file
but if application got restarted then it may be vary for first back file.

**How to run it for AWS**
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
  "NUMBER_OF_KAFKA_THREADS": 3,
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
  "NUMBER_OF_KAFKA_THREADS": 3,
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
{ "@timestamp": "2020-06-10 12:49:43,871","level": "INFO","thread": "S3 Upload","name": "botocore.credentials","message": "Found credentials in environment variables." }
{ "@timestamp": "2020-06-10 12:49:43,912","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-10 12:49:43,915","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-10 12:49:43,916","level": "INFO","thread": "Kafka Consumer 2","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2020-06-10 12:49:44,307","level": "INFO","thread": "S3 Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/0/20200608-102909.tar.gz" }
{ "@timestamp": "2020-06-10 12:49:45,996","level": "INFO","thread": "S3 Upload","name": "root","message": "waiting for new files to be generated" }
{ "@timestamp": "2020-06-10 12:52:33,130","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/0/20200610-125233.tar.gz" }
{ "@timestamp": "2020-06-10 12:52:33,155","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/0/20200610-125233.tar.gz.sha256" }
....
```

**Backup Application Directory Structure**
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

# Kafka Restore Application

* it will restore from backup dir into given topic.
* `RETRY_SECONDS` controls when to reread `FILESYSTEM_BACKUP_DIR` for new files and download from S3 as well.
* `RESTORE_PARTITION_STRATEGY` controls, in which partition it will restore messages. if **`same`** is mentioned then it will restore into same topic partition but if **`random`** is mentioned then it will restore to all partitions randomly.

**Known Issues**
* Restore application can't read from already extracted file which means if previous run failed while restoring content from xxx.bin file then it won't resume from same file.

**How to run it**
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
  "RETRY_SECONDS": 100,
  "RESTORE_PARTITION_STRATEGY": "same/random"
}
```

**S3 Filesytem Restore.json**
```
{
  "BOOTSTRAP_SERVERS": "kafka01:9092,kafka02:9092,kafka03:9092",
  "BACKUP_TOPIC_NAME": "davinder.test",
  "RESTORE_TOPIC_NAME": "davinder-restore.test",
  "FILESYSTEM_TYPE": "S3",
  "BUCKET_NAME": "davinder-test-kafka-backup",
  "FILESYSTEM_BACKUP_DIR": "/tmp",
  "RETRY_SECONDS": 100,
  "RESTORE_PARTITION_STRATEGY": "same/random"
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

**Example S3 Restore Run Output**
```
$ python3 restore.py restore.json
{ "@timestamp": "2020-06-17 13:13:45,986","level": "INFO","thread": "S3 Download","name": "botocore.credentials","message": "Found credentials in environment variables." }
{ "@timestamp": "2020-06-17 13:13:46,416","level": "INFO","thread": "S3 Download","name": "root","message": "retry for new file after 100s in s3://davinder-test-kafka-backup/davinder.test" }
{ "@timestamp": "2020-06-17 13:13:58,849","level": "INFO","thread": "Kafka Producer","name": "root","message": "restore successful of file /tmp/davinder.test/1/20200611-104925.tar.gz" }
{ "@timestamp": "2020-06-17 13:15:26,651","level": "INFO","thread": "S3 Download","name": "root","message": "retry for new file after 100s in s3://davinder-test-kafka-backup/davinder.test" }
....
```

**Restore Application Directory Structure [ Temporary ]**
```
/tmp/davinder.test/
├── 0
│   ├── 20200611-101529.tar.gz
│   ├── 20200611-101529.tar.gz.sha256
│   └── checkpoint
├── 1
│   ├── 20200611-101532.tar.gz
│   ├── 20200611-101532.tar.gz.sha256
│   └── checkpoint
└── 2
    ├── 20200611-101531.tar.gz
    ├── 20200611-101531.tar.gz.sha256
    ├── 20200611-101534.tar.gz
    ├── 20200611-101534.tar.gz.sha256
    └── checkpoint
```
