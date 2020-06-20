import os
import logging

def read_checkpoint_partition(dir,topic,partition):
    """It will read checkpoint file for given topic and partition."""

    try:
        logging.debug(os.path.join(dir,topic,partition,"checkpoint"))
        with open(os.path.join(dir,topic,partition,"checkpoint")) as c:
            line = c.readline().strip()
            _ck_file = line.split()[0]
            _total_files = line.split()[1]
            return {"checkpoint": _ck_file, "total_files": _total_files}
    except FileNotFoundError as e:
        logging.error(e)
    return None

def write_checkpoint_partition(dir,topic,partition,msg):
    """It will write checkpoint message for given topic and partition to given checkpoint file"""

    try:
        with open(os.path.join(dir,topic,partition,"checkpoint"), "w") as cp:
            cp.write(msg)
    except TypeError as e:
        logging.error(e)
        logging.error(f"writing checkpoint {msg} for {topic}, {partition} is failed")