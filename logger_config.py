import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_logger(name):
    return logging.getLogger(name)