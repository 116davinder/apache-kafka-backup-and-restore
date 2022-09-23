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

* It will take backup of given topic and store that into Azure Blob Storage.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to container which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* `RETRY_UPLOAD_SECONDS` controls upload to Azure Blob Storage.
* `NUMBER_OF_KAFKA_THREADS` is used to parallelise reading from kafka topic.
It should not be more than number of partitions.
* `NUMBER_OF_MESSAGE_PER_BACKUP_FILE` will try to keep this number consistent in file
but if application got restarted then it may be vary for first back file.

**How to run it for Azure**
```
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=davindertestingpython;AccountKey=xxxx==;EndpointSuffix=core.windows.net"

python3 backup.py examples-jsons/backup-azure.json
```

**Azure Blob Storage Backup.json**
```json
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "TOPIC_NAMES": ["davinder.test"],
  "GROUP_ID": "Kafka-BackUp-Consumer-Group",
  "CONTAINER_NAME": "kafka-backup",
  "FILESYSTEM_TYPE": "AZURE",
  "FILESYSTEM_BACKUP_DIR": "/tmp/",
  "NUMBER_OF_MESSAGE_PER_BACKUP_FILE": 1000,
  "RETRY_UPLOAD_SECONDS": 100,
  "NUMBER_OF_KAFKA_THREADS": 2,
  "LOG_LEVEL": 20
}
```

**Example Azure Backup Run Output**
```json
$ python3 backup.py example-jsons/backup-azure.json
{ "@timestamp": "2022-04-25 11:05:27,545","level": "INFO","thread": "Kafka Consumer 0","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2022-04-25 11:05:27,545","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "started polling on davinder.test" }
{ "@timestamp": "2022-04-25 11:05:27,658","level": "INFO","thread": "MainThread","name": "root","message": "Azure upload retry for new files in 100 seconds" }
{ "@timestamp": "2022-04-25 11:07:06,009","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backupfile /tmp/davinder.test/2/20220425-110705.tar.gz" }
{ "@timestamp": "2022-04-25 11:07:06,010","level": "INFO","thread": "Kafka Consumer 1","name": "root","message": "Created Successful Backup sha256 file of /tmp/davinder.test/2/20220425-110705.tar.gz.sha256" }
{ "@timestamp": "2022-04-25 11:07:07,759","level": "INFO","thread": "Azure Upload Threads /tmp/davinder.test/0/20220425-110635.tar.gz.sha256","name": "azure.core.pipeline.policies.http_logging_policy","message": "Request URL: 'https://davindertestingpython.blob.core.windows.net/kafka-backup/davinder.test/0/20220425-110635.tar.gz.sha256'
Request method: 'PUT'
Request headers:
    'x-ms-blob-type': 'REDACTED'
    'Content-Length': '64'
    'If-None-Match': '*'
    'x-ms-version': 'REDACTED'
    'Content-Type': 'application/octet-stream'
    'Accept': 'application/xml'
    'User-Agent': 'azsdk-python-storage-blob/12.11.0 Python/3.9.7 (Linux-5.13.0-40-generic-x86_64-with-glibc2.34)'
    'x-ms-date': 'REDACTED'
    'x-ms-client-request-id': 'b37095ac-c46e-11ec-a672-671a56d4a63c'
    'Authorization': 'REDACTED'
A body is sent with the request" }
{ "@timestamp": "2022-04-25 11:07:09,041","level": "INFO","thread": "Azure Upload Threads /tmp/davinder.test/1/20220425-110606.tar.gz","name": "root","message": "upload successful /tmp/davinder.test/1/20220425-110606.tar.gz" }
{ "@timestamp": "2022-04-25 11:08:47,903","level": "INFO","thread": "MainThread","name": "root","message": "Azure upload retry for new files in 100 seconds" }
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
* `RETRY_SECONDS` controls when to reread `FILESYSTEM_BACKUP_DIR` for new files and download from Azure Blob Storage as well.
* `RESTORE_PARTITION_STRATEGY` controls, in which partition it will restore messages. if **`same`** is mentioned then it will restore into same topic partition but if **`random`** is mentioned then it will restore to all partitions randomly.

**How to run it**
```
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=davindertestingpython;AccountKey=xxxx==;EndpointSuffix=core.windows.net"

python3 restore.py examples-jsons/restore-azure.json
```

**Azure Blob Storage Restore.json**
```json
{
  "BOOTSTRAP_SERVERS": "localhost:9092",
  "BACKUP_TOPIC_NAME": "davinder.test1",
  "RESTORE_TOPIC_NAME": "davinder-restore.test",
  "FILESYSTEM_TYPE": "AZURE",
  "CONTAINER_NAME": "kafka-backup",
  "FILESYSTEM_BACKUP_DIR": "/tmp",
  "RETRY_SECONDS": 100,
  "RESTORE_PARTITION_STRATEGY": "random",
  "LOG_LEVEL": 20
}
```

**Example Azure Blob Storage Restore Run Output**
```json
$ python3 restore.py example-jsons/restore-azure.json
{ "@timestamp": "2022-04-26 16:43:16,899","level": "INFO","thread": "Azure Download","name": "azure.core.pipeline.policies.http_logging_policy","message": "Request URL: 'https://davindertestingpython.blob.core.windows.net/kafka-backup?restype=REDACTED&comp=REDACTED&prefix=REDACTED&delimiter=REDACTED'
Request method: 'GET'
Request headers:
    'x-ms-version': 'REDACTED'
    'Accept': 'application/xml'
    'User-Agent': 'azsdk-python-storage-blob/12.11.0 Python/3.9.7 (Linux-5.13.0-40-generic-x86_64-with-glibc2.34)'
    'x-ms-date': 'REDACTED'
    'x-ms-client-request-id': 'd398e9a8-c566-11ec-a672-671a56d4a63c'
    'Authorization': 'REDACTED'
No body was attached to the request" }
{ "@timestamp": "2022-04-26 16:43:16,903","level": "INFO","thread": "Kafka Restore Thread","name": "root","message": "retry for more files in /tmp/davinder.test after 100" }
{ "@timestamp": "2022-04-26 16:43:17,981","level": "INFO","thread": "Azure Download","name": "root","message": "Total Files: 4, partition: 0, files to download: 0" }
{ "@timestamp": "2022-04-26 16:43:18,105","level": "INFO","thread": "Azure Download","name": "root","message": "Total Files: 7, partition: 1, files to download: 0" }
{ "@timestamp": "2022-04-26 16:43:18,106","level": "INFO","thread": "Azure Download","name": "azure.core.pipeline.policies.http_logging_policy","message": "Request URL: 'https://davindertestingpython.blob.core.windows.net/kafka-backup?restype=REDACTED&comp=REDACTED&prefix=REDACTED&delimiter=REDACTED'
Request method: 'GET'
Request headers:
    'x-ms-version': 'REDACTED'
    'Accept': 'application/xml'
    'User-Agent': 'azsdk-python-storage-blob/12.11.0 Python/3.9.7 (Linux-5.13.0-40-generic-x86_64-with-glibc2.34)'
    'x-ms-date': 'REDACTED'
    'x-ms-client-request-id': 'd4510b32-c566-11ec-a672-671a56d4a63c'
    'Authorization': 'REDACTED'
No body was attached to the request" }
{ "@timestamp": "2022-04-26 16:43:18,264","level": "INFO","thread": "Azure Download","name": "azure.core.pipeline.policies.http_logging_policy","message": "Response status: 200
Response headers:
    'Transfer-Encoding': 'chunked'
    'Content-Type': 'application/xml'
    'Server': 'Windows-Azure-Blob/1.0 Microsoft-HTTPAPI/2.0'
    'x-ms-request-id': '6169f165-501e-0051-3a73-59df81000000'
    'x-ms-client-request-id': 'd4510b32-c566-11ec-a672-671a56d4a63c'
    'x-ms-version': 'REDACTED'
    'Date': 'Tue, 26 Apr 2022 13:43:17 GMT'" }
{ "@timestamp": "2022-04-26 16:43:18,266","level": "INFO","thread": "Azure Download","name": "root","message": "Total Files: 5, partition: 2, files to download: 0" }
{ "@timestamp": "2022-04-26 16:43:18,267","level": "INFO","thread": "Azure Download","name": "root","message": "retry for new file after 100s in Azure kafka-backup/davinder.test" }
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
