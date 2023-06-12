import logging
import tracker
import time

if __name__ == '__main__':
    logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("files/alert.log"),
        logging.StreamHandler()
    ])
    
    while True:
        tracker.update_all()
        logging.debug("Updated all packages")
        conf = tracker.read_config("files/config.json")
        if "config" in conf:
            interval = conf["config"].get("interval")
            if not interval:
                interval = 60
            time.sleep(interval)
            
