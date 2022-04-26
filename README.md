# Apache Kafka Backup and Restore

**Production Kafka Deployment Using Ansible**
* https://github.com/116davinder/kafka-cluster-ansible/wiki

**General Notes**
* `LOG_LEVEL` values can be found https://docs.python.org/3/library/logging.html#logging-levels

## Requirements
* confluent-kafka
* boto3
* azure-storage-blob

# Kafka Backup Application

* It will take backup of given topic and store that into either local filesystem or S3 or Azure.
* It will auto resume from same point from where it died if given consumer group name is same before and after crash.
* it will upload `current.bin` file to s3 which contains messages upto `NUMBER_OF_MESSAGE_PER_BACKUP_FILE`
but will only upload with other backup files.
* `RETRY_UPLOAD_SECONDS` controls upload to cloud storage.
* `NUMBER_OF_KAFKA_THREADS` is used to parallelise reading from kafka topic.
It should not be more than number of partitions.
* `NUMBER_OF_MESSAGE_PER_BACKUP_FILE` will try to keep this number consistent in file
but if application got restarted then it may be vary for first back file.

# Kafka Restore Application

* it will restore from backup dir into given topic.
* `RETRY_SECONDS` controls when to reread `FILESYSTEM_BACKUP_DIR` for new files.
* `RESTORE_PARTITION_STRATEGY` controls, in which partition it will restore messages. if **`same`** is mentioned then it will restore into same topic partition but if **`random`** is mentioned then it will restore to all partitions randomly.

**Known Issues**
* Restore application can't read from already extracted file which means if previous run failed while restoring content from xxx.bin file then it won't resume from same file.

## How to Run Applications
[Azure Cloud Readme](./README-Azure.md)

[AWS Cloud Readme](./README-AWS.md)

[Local Readme](./README-Local.md)
