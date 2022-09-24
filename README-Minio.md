# How to Run with MINIO

**General Notes**
* `LOG_LEVEL` values can be found https://docs.python.org/3/library/logging.html#logging-levels
* `If there are too many get/put requests to MINIO then increase NUMBER_OF_MESSAGE_PER_BACKUP_FILE to reduce minio requests.`

## Requirements
* confluent-kafka
* minio

## Development with Docker
Ref: https://min.io/docs/minio/container/index.html
```
docker run --rm \
   -p 9000:9000 \
   -p 9090:9090 \
   --name minio \
   -e "MINIO_ROOT_USER=minio" \
   -e "MINIO_ROOT_PASSWORD=CHANGEME123" \
   quay.io/minio/minio server /data --console-address ":9090"
```

# Kafka Backup Application

* It will take backup of given topic and store that into temp local filesystem then upload to MINIO.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* `RETRY_UPLOAD_SECONDS` controls upload to s3 or other cloud storage.
* `NUMBER_OF_KAFKA_THREADS` is used to parallelise reading from kafka topic.
It should not be more than number of partitions.
* `NUMBER_OF_MESSAGE_PER_BACKUP_FILE` will try to keep this number consistent in file
but if application got restarted then it may be vary for first back file.

**How to run it for MINIO**
```bash
export MINIO_ACCESS_KEY="ZBPIIAOCJRY9QLUVEHQO"
export MINIO_SECRET_KEY="vMIoCaBu9sSg4ODrSkbD9CGXtq0TTpq6kq7psLuE"

python3 backup.py example-jsons/backup-minio.json
```

**MINIO backup.json**
```json
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "FILESYSTEM_TYPE": "MINIO",
  "MINIO_URL": "localhost:9000",
  "IS_MINIO_SECURE": "False",
  "BUCKET_NAME": "kafka-backup",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 1000,
  "RETRY_UPLOAD_SECONDS": 100,
  "NUMBER_OF_KAFKA_THREADS": 2,
  "LOG_LEVEL": 20
}
```

**Example MINIO Backup Run Output**
```bash
$ python3 backup.py example-jsons/backup-minio.json
{ "@timestamp": "2022-09-23 21:05:43,713","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2022-09-23 21:05:43,714","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2022-09-23 21:05:43,780","level": "INFO","thread": "MainThread","name": "root","message": "minio upload retry for new files in 100 seconds" }
{ "@timestamp": "2022-09-23 21:05:43,789","level": "INFO","thread": "MINIO Upload Threads","name": "root","message": "upload successful at minio://kafka-backup/davinder.test/0/20220923-205800.tar.gz.sha256" }
{ "@timestamp": "2022-09-23 21:05:43,790","level": "INFO","thread": "MINIO Upload Threads","name": "root","message": "upload successful at minio://kafka-backup/davinder.test/0/20220923-205800.tar.gz" }
{ "@timestamp": "2022-09-23 21:06:21,163","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/1/20220923-210621.tar.gz" }
{ "@timestamp": "2022-09-23 21:06:21,163","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/1/20220923-210621.tar.gz.sha256" }
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
* `RETRY_SECONDS` controls when to reread `FILESYSTEM_BACKUP_DIR` for new files and download from minio as well.
* `RESTORE_PARTITION_STRATEGY` controls, in which partition it will restore messages. if **`same`** is mentioned then it will restore into same topic partition but if **`random`** is mentioned then it will restore to all partitions randomly.

**How to run it**
```bash
export MINIO_ACCESS_KEY="ZBPIIAOCJRY9QLUVEHQO"
export MINIO_SECRET_KEY="vMIoCaBu9sSg4ODrSkbD9CGXtq0TTpq6kq7psLuE"

python3 restore.py example-jsons/restore-minio.json
```

**MINIO Filesytem Restore.json**
```json
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "BACKUP_TOPIC_NAME": "davinder.test",
  "RESTORE_TOPIC_NAME": "davinder-restore.test",
  "FILESYSTEM_TYPE": "MINIO",
  "MINIO_URL": "localhost:9000",
  "IS_MINIO_SECURE": "False",
  "BUCKET_NAME": "kafka-backup",
  "FILESYSTEM_BACKUP_DIR": "/tmp",
  "RETRY_SECONDS": 100,
  "RESTORE_PARTITION_STRATEGY": "same",
  "LOG_LEVEL": 20
}
```

**Example MINIO Restore Run Output**
```bash
$ python3 restore.py example-jsons/restore-minio.json
{ "@timestamp": "2022-09-23 23:03:22,201","level": "INFO","thread": "Minio Download","name": "root","message": "retry for new file after 100s in minio://kafka-backup/davinder.test" }
{ "@timestamp": "2022-09-23 23:03:23,308","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "restore successful of file /tmp/davinder.test/0/20220923-210652.tar.gz" }
{ "@timestamp": "2022-09-23 23:03:23,433","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "restore successful of file /tmp/davinder.test/0/20220923-210705.tar.gz" }
{ "@timestamp": "2022-09-23 23:03:23,544","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "restore successful of file /tmp/davinder.test/0/20220923-210847.tar.gz" }
{ "@timestamp": "2022-09-23 23:04:02,396","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "restore successful of file /tmp/davinder.test/2/20220923-210823.tar.gz" }
{ "@timestamp": "2022-09-23 23:04:02,592","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "restore successful of file /tmp/davinder.test/2/20220923-210714.tar.gz" }
{ "@timestamp": "2022-09-23 23:04:02,592","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "retry for more files in /tmp/davinder.test after 100" }
{ "@timestamp": "2022-09-23 23:05:02,332","level": "INFO","thread": "Minio Download","name": "root","message": "retry for new file after 100s in minio://kafka-backup/davinder.test" }
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
