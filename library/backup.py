import confluent_kafka
from common import common
import logging
import os


class KBackup:
    def __init__(self, config):
        """initialize variables"""
        self.BOOTSTRAP_SERVERS = config['BOOTSTRAP_SERVERS']
        self.GROUP_ID = config['GROUP_ID']
        self.TOPIC_NAME_LIST = config['TOPIC_NAMES']
        self.BACKUP_DIR = os.path.join(config['FILESYSTEM_BACKUP_DIR'], self.TOPIC_NAME_LIST[0])
        try:
            self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = int(config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])
        except (ValueError, KeyError):
            logging.error(
                f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE {str(config['NUMBER_OF_MESSAGE_PER_BACKUP_FILE'])} is not integer value"
            )
            self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE = 1000
            logging.info(f"NUMBER_OF_MESSAGE_PER_BACKUP_FILE is set to default value {self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE}")
        try:
            self.NUMBER_OF_KAFKA_THREADS = config['NUMBER_OF_KAFKA_THREADS']
        except KeyError:
            self.NUMBER_OF_KAFKA_THREADS = 1
        self.CONSUMERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'group.id': self.GROUP_ID,
            'auto.offset.reset': 'earliest'
        }
        try:
            self.LOG_LEVEL = config['LOG_LEVEL']
        except KeyError:
            self.LOG_LEVEL = logging.INFO

        logging.debug("successful loading of kafka variables")

    def backup(self):
        _bt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _bt.subscribe(self.TOPIC_NAME_LIST)

        for p in common.findNumberOfPartitionsInTopic(_bt.list_topics().topics[self.TOPIC_NAME_LIST[0]].partitions):
            os.makedirs(os.path.join(self.BACKUP_DIR, str(p)), exist_ok=True)

        count = 0
        logging.info(f"started polling on {self.TOPIC_NAME_LIST[0]}")
        while True:
            msg = _bt.poll(timeout=1.0)
            if msg is None:
                logging.debug(f"waiting for new messages from topic {self.TOPIC_NAME_LIST[0]}")
                continue
            if msg.error():
                logging.error(f"{msg.error()}")
                continue
            if msg.partition() is not None:
                _tmp_file = os.path.join(self.BACKUP_DIR, str(msg.partition()), "current.bin")
                _tar_location = os.path.join(self.BACKUP_DIR, str(msg.partition()))
                _msg = common.decodeMsgToUtf8(msg)
                if _msg is not None:
                    if count == 0:
                        common.writeDataToKafkaBinFile(_tmp_file, _msg, "a+")
                    if count > 0:
                        if count % self.NUMBER_OF_MESSAGE_PER_BACKUP_FILE == 0:
                            common.createTarGz(_tar_location, _tmp_file)
                            common.writeDataToKafkaBinFile(_tmp_file, _msg, "w")
                            count = 0
                        else:
                            common.writeDataToKafkaBinFile(_tmp_file, _msg, "a+")
            else:
                logging.error("no partition found for message")

            count += 1

        _bt.close()

