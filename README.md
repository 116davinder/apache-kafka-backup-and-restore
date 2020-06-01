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
$ python3 backup.py config.json
{ "@timestamp": "2020-05-31 18:54:18,765","level": "INFO","thread": "MainThread","name": "root","message": "Successful loading of config.json file" }
{ "@timestamp": "2020-05-31 18:54:18,766","level": "INFO","thread": "MainThread","name": "root","message": "all required variables are successfully set from config.json" }
{ "@timestamp": "2020-05-31 18:54:18,770","level": "INFO","thread": "Kafka Consumer","name": "root","message": "topic folder already exists /tmp/davinder.test" }
{ "@timestamp": "2020-05-31 18:54:18,785","level": "INFO","thread": "Kafka Consumer","name": "root","message": "starting polling on ['davinder.test']" }
{ "@timestamp": "2020-05-31 18:54:18,798","level": "INFO","thread": "S3-Upload","name": "botocore.credentials","message": "Found credentials in environment variables." }
{ "@timestamp": "2020-05-31 18:54:18,922","level": "INFO","thread": "S3-Upload","name": "root","message": "waiting for new files to be generated" }
{ "@timestamp": "2020-05-31 18:54:46,433","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200531-185446.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:46,435","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200531-185446.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:47,260","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200531-185447.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:47,262","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200531-185447.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:48,265","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/20200531-185448.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:48,266","level": "INFO","thread": "Kafka Consumer","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/20200531-185448.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:49,235","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185446.tar.gz at destination path davinder.test/20200531-185446.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:49,330","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185446.tar.gz.sha256 at destination path davinder.test/20200531-185446.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:49,419","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185447.tar.gz at destination path davinder.test/20200531-185447.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:49,510","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185447.tar.gz.sha256 at destination path davinder.test/20200531-185447.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:49,601","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185448.tar.gz at destination path davinder.test/20200531-185448.tar.gz" }
{ "@timestamp": "2020-05-31 18:54:49,695","level": "INFO","thread": "S3-Upload","name": "root","message": "upload done for /tmp/davinder.test/20200531-185448.tar.gz.sha256 at destination path davinder.test/20200531-185448.tar.gz.sha256" }
{ "@timestamp": "2020-05-31 18:54:49,697","level": "INFO","thread": "S3-Upload","name": "root","message": "waiting for new files to be generated" }
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
