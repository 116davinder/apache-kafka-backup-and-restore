import confluent_kafka
from os import sys
from common import Common
import logging

class KBackup:
    def __init__(self,configFilePath):

        _config = Common.readJsonConfig(configFilePath)
        if _config is not None:
            self.BOOTSTRAP_SERVERS = _config['BOOTSTRAP_SERVERS']
            self.GROUP_ID = _config['GROUP_ID']
            self.TOPIC_NAME_LIST = _config['TOPIC_NAMES']
            self.BACKUP_DIR = _config['FILESYSTEM_BACKUP_DIR'] + self.TOPIC_NAME_LIST[0]
            self.BACKUP_TMP_FILE = self.BACKUP_DIR + "/current.bin"
            self.FILESYSTEM_TYPE = _config['FILESYSTEM_TYPE']
            try:
                self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = int(_config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])
            except:
                logging.info(f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE {str(_config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])} is not integer value")
                self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = 50
                logging.info(f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE is set to default value 50")

            self.CONSUMERCONFIG = {
                'bootstrap.servers': self.BOOTSTRAP_SERVERS,
                'group.id': self.GROUP_ID,
                'auto.offset.reset': 'earliest'
            }
            logging.info(f"all required variables are sucessfully set from {configFilePath}")
        else:
            logging.error(f"all required variables are not sucessfully set from {configFilePath}")

    def readFromTopic(self):
        _rt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _rt.subscribe(self.TOPIC_NAME_LIST)

        Common.createBackupTopicDir(self.BACKUP_DIR)

        count = Common.currentMessageCountInBinFile(self.BACKUP_TMP_FILE)

        while True:
            msg = _rt.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error(f"{msg.error()}")
                continue

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
            _rt.commit(asynchronous=False)

        _rt.close()

def main():
    logging.basicConfig(
        format='{ "@timestamp": "%(asctime)s","level": "%(levelname)s","name": "%(name)s","message": "%(message)s" }'
    )
    logging.getLogger().setLevel(logging.INFO)

    configFilePath = sys.argv[1]
    b = KBackup(configFilePath)
    b.readFromTopic()

main()
