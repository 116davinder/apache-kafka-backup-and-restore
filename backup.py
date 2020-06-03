import confluent_kafka
import os
from common import Common
import logging
import threading
from upload import Upload

class KBackup:
    def __init__(self,config):

        self.BOOTSTRAP_SERVERS = config['BOOTSTRAP_SERVERS']
        self.GROUP_ID = config['GROUP_ID']
        self.TOPIC_NAME_LIST = config['TOPIC_NAMES']
        self.BACKUP_DIR = os.path.join(config['FILESYSTEM_BACKUP_DIR'], self.TOPIC_NAME_LIST[0])
        self.BACKUP_TMP_FILE = os.path.join(self.BACKUP_DIR, "current.bin")
        try:
            self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = int(config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])
        except:
            logging.info(
                f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE {str(config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])} is not integer value"
            )
            self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = 50
            logging.info(f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE is set to default value 50")

        self.CONSUMERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'group.id': self.GROUP_ID,
            'auto.offset.reset': 'earliest'
        }
        logging.info(f"successful loading of all variables")

    def readFromTopic(self):
        _rt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _rt.subscribe(self.TOPIC_NAME_LIST)

        Common.createBackupTopicDir(self.BACKUP_DIR)

        count = Common.currentMessageCountInBinFile(self.BACKUP_TMP_FILE)
        logging.info(f"started polling on {self.TOPIC_NAME_LIST[0]}")
        while True:
            msg = _rt.poll(timeout=1.0)
            if msg is None:
                logging.debug(f"waiting for new messages from topic {self.TOPIC_NAME_LIST[0]}")
                continue
            if msg.error():
                logging.error(f"{msg.error()}")
                continue
            else:
                _msg = Common.decodeMsgToUtf8(msg)
                if _msg is not None:
                    if count == 0:
                        Common.writeDataToKafkaBinFile(self.BACKUP_TMP_FILE, _msg, "a+")
                    if count > 0:
                        if count % self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE == 0:
                            Common.createTarGz(self.BACKUP_DIR, self.BACKUP_TMP_FILE)
                            Common.writeDataToKafkaBinFile(self.BACKUP_TMP_FILE, _msg, "w")
                        else:
                            Common.writeDataToKafkaBinFile(self.BACKUP_TMP_FILE, _msg, "a+")
            
            count += 1

        _rt.close()


def main():

    Common.setLoggingFormat()
    try:
        config = Common.readJsonConfig(os.sys.argv[1])
    except IndexError as e:
        logging.error(f"backup.json is not passed")
        exit(1)

    b = KBackup(config)
    _r_thread = threading.Thread(
        target=b.readFromTopic,
        name="Kafka Consumer"
    )
    _r_thread.start()

    if config['FILESYSTEM_TYPE'] == "S3":
        try:
            bucket = config['BUCKET_NAME']
            tmp_dir = config['FILESYSTEM_BACKUP_DIR']
            topic_name = config['TOPIC_NAMES'][0]
            try:
                retry_upload_seconds = config['RETRY_UPLOAD_SECONDS']
                logging.info(f"RETRY_UPLOAD_SECONDS is set to {config['RETRY_UPLOAD_SECONDS']}")
            except:
                logging.info(f"setting RETRY_UPLOAD_SECONDS to default 60 ")
                retry_upload_seconds = 60
            _s3_upload_thread = threading.Thread(
                target=Upload.s3_upload_files,
                args=[bucket, tmp_dir, topic_name,retry_upload_seconds],
                name="S3-Upload"
            )
            _s3_upload_thread.start()
        except KeyError as e:
            logging.error(f"unable to set s3 required variables {e}")

if __name__ == "__main__":
    main()
