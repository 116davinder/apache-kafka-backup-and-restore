from common import Common
import os
import logging

class KRestore:

    def __init__(self,config):
        self.BOOTSTRAP_SERVERS = config['BOOTSTRAP_SERVERS']
        self.RESTORE_TOPIC_NAME = config['RESTORE_TOPIC_NAME']
        self.BACKUP_DIR = config['FILESYSTEM_BACKUP_DIR']
        self.BACKUP_TMP_FILE = os.path.join(self.BACKUP_DIR, "current.bin")
        self.PRODUCERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS
        }
        logging.info(f"successful loading of all variables")

    def matchHashforFiles(self):
        _hash_matched_files_list = []
        try:
            _list_all_Files = os.listdir(self.BACKUP_DIR)
            if len(_list_all_Files) > 0:
                for file in _list_all_Files:
                    if file.endswith("tar.gz"):
                        _current_file_path = os.path.join(self.BACKUP_DIR , file)
                        _current_file_hash = Common.calculateSha256(_current_file_path)
                        if Common.compareSha256withFile(_current_file_path,_current_file_hash):
                            _hash_matched_files_list.append(_current_file_path)
                        else:
                            logging.error(f"hash value from {_current_file_path}.sha256 didn't matched with {_current_file_hash}")
        except FileNotFoundError as e:
            logging.error(e)
        
        return sorted(_hash_matched_files_list)

def main():

    Common.setLoggingFormat()

    try:
        config = Common.readJsonConfig(os.sys.argv[1])
    except IndexError as e:
        logging.error(f"restore.json is not passed")
        exit(1)

    b = KRestore(config)
    print(b.matchHashforFiles())

main()