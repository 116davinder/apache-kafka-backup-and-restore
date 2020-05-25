import confluent_kafka
from datetime import datetime
import tarfile
import hashlib
from os import mkdir

class KBackup:
    def __init__(self):
        self.BOOTSTRAP_SERVERS = 'localhost:9092'
        self.CONSUMERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'group.id': "Kafka-BackUp-Consumer-Group",
            'auto.offset.reset': 'earliest'
        }
        self.TOPIC_NAME_LIST = ["davinder.test"]
        self.BACKUP_DIR = "/tmp/" + self.TOPIC_NAME_LIST[0]
        self.BACKUP_TMP_FILE = self.BACKUP_DIR + "/current.bin"

    def __calculateSha256(self, file):
        with open(file,"rb") as f:
            return hashlib.sha256(f.read()).hexdigest();

    def __createSha256OfBackupFile(self, file):
        with open(file + ".sha256", "w") as f:
            f.write(self.__calculateSha256(file))

    def __writeDataToKafkaBinFile(self,msg,mode):
        with open(self.BACKUP_TMP_FILE, mode) as f:
            f.write(msg.value().decode('utf-8'))
            f.write("\n")

    def __createTarGz(self):
        file = self.BACKUP_DIR + "/" + datetime.now().strftime("%Y%M%d-%H%M%S") + ".tar.gz"
        _t = tarfile.open(file, "w:gz")
        _t.add(self.BACKUP_TMP_FILE)
        _t.close()
        self.__createSha256OfBackupFile(file)

    def __createBackupTopicDir(self):
        try:
            mkdir(self.BACKUP_DIR)
        except FileExistsError:
            pass

    def readFromTopic(self):
        _rt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _rt.subscribe(self.TOPIC_NAME_LIST)

        self.__createBackupTopicDir()

        count = 0
        while True:
            msg = _rt.poll(timeout=5.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer Error: {msg.error()}")
                continue

            if count == 0:
                self.__writeDataToKafkaBinFile(msg, "a+")
            if count > 0:
                if count % 50 == 0:
                    self.__createTarGz()
                    self.__writeDataToKafkaBinFile(msg, "w")
                else:
                    self.__writeDataToKafkaBinFile(msg, "a+")
            count += 1

        _rt.close()

def main():
    b = KBackup()
    b.readFromTopic()

main()
