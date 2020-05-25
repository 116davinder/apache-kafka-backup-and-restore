import confluent_kafka
from datetime import datetime
import tarfile
import os

class KBackup:
    def __init__(self):
        self.BOOTSTRAP_SERVERS = 'localhost:9092'
        self.CONSUMERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'group.id': "Kafka-BackUp-Consumer-Group",
            'auto.offset.reset': 'earliest'
        }
        self.TMPFILE = "/tmp/kafka-backup.bin"

    # def backupMd5Sum():
        # it should create md5sum file for each backup file

    def readFromTopic(self):
        _rt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _rt.subscribe(["davinder.test"])

        count = 0
        while True:
            msg = _rt.poll(timeout=5.0)

            if msg is None:
                continue
            if msg.error():
                print(f"Consumer Error: {msg.error()}")
                continue

            print(f"Recieved Message: {msg.value().decode('utf-8')}")
            print(f"Current Poll Count: {count}")
            if count == 0:
                with open(self.TMPFILE, "a+") as f:
                    f.write(msg.value().decode('utf-8'))
                    f.write("\n")
            if count > 0:
                if count % 50 == 0:
                    print(f"Creating Tar of Last 50 Messages")
                    filename = datetime.now().strftime('%Y%M%d-%H%M%S') + '.tar.gz'
                    _t = tarfile.open('/tmp/' + filename, "w:gz")
                    _t.add(self.TMPFILE)
                    _t.close()
                    with open(self.TMPFILE, "w") as f:
                        f.write(msg.value().decode('utf-8'))
                        f.write("\n")
                else:
                    print("Appending Data to File")
                    with open(self.TMPFILE, "a+") as f:
                        f.write(msg.value().decode('utf-8'))
                        f.write("\n")

            count += 1

        _rt.close()

def main():
    b = KBackup()
    b.readFromTopic()

main()
