# apache-kafka-backup-and-restore
It will take backup of given topic and store that into either local filesystem or S3.

It will auto resume from same point from where it died if given consumer group name is same before and after crash.

**Note**
* it won't upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE - 1`.
* upload to s3 is async method.

## Requirements
* confluent-kafka
* boto3

# How to Run it
```
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXX
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXX

python3 backup.py backup.json
```

**Local Filesytem Backup backup.json**
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

**S3 Backup backup.json**
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

**Example Run Output**
```
$ python3 backup.py backup.json
{ "@timestamp": "2020-06-01 10:37:00,168","level": "INFO","thread": "MainThread","name": "root","message": "Successful loading of config.json file" }
{ "@timestamp": "2020-06-01 10:37:00,169","level": "INFO","thread": "MainThread","name": "root","message": "all required variables are successfully" }
{ "@timestamp": "2020-06-01 10:37:00,174","level": "INFO","thread": "Kafka Consumer","name": "root","message": "topic folder already exists /tmp/davinder.test" }
{ "@timestamp": "2020-06-01 10:37:00,187","level": "INFO","thread": "Kafka Consumer","name": "root","message": "starting polling on davinder.test" }
{ "@timestamp": "2020-06-01 10:37:00,217","level": "INFO","thread": "S3-Upload","name": "botocore.credentials","message": "Found credentials in environment variables." }
{ "@timestamp": "2020-06-01 10:37:00,324","level": "INFO","thread": "S3-Upload","name": "root","message": "waiting for new files to be generated" }
{ "@timestamp": "2020-06-01 10:38:00,325","level": "INFO","thread": "S3-Upload","name": "root","message": "waiting for new files to be generated" }
{ "@timestamp": "2020-06-01 10:38:17,291","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103817.tar.gz" }
{ "@timestamp": "2020-06-01 10:38:17,294","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200601-103817.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:38:18,223","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103818.tar.gz" }
{ "@timestamp": "2020-06-01 10:38:18,226","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200601-103818.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:38:19,044","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103819.tar.gz" }
{ "@timestamp": "2020-06-01 10:38:19,048","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200601-103819.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:38:19,974","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103819.tar.gz" }
{ "@timestamp": "2020-06-01 10:38:19,977","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200601-103819.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:38:20,961","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200601-103820.tar.gz" }
{ "@timestamp": "2020-06-01 10:38:20,963","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200601-103820.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:39:00,631","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103817.tar.gz" }
{ "@timestamp": "2020-06-01 10:39:00,747","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103817.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:39:01,084","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103818.tar.gz" }
{ "@timestamp": "2020-06-01 10:39:01,182","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103818.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:39:01,301","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103819.tar.gz" }
{ "@timestamp": "2020-06-01 10:39:01,427","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103819.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:39:01,520","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103820.tar.gz" }
{ "@timestamp": "2020-06-01 10:39:01,617","level": "INFO","thread": "S3-Upload","name": "root","message": "upload successful at s3://davinder-test-kafka-backup/davinder.test/20200601-103820.tar.gz.sha256" }
{ "@timestamp": "2020-06-01 10:39:01,620","level": "INFO","thread": "S3-Upload","name": "root","message": "waiting for new files to be generated" }
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
