# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import logging

class BlankFormatter(logging.Formatter):
    def format(self, record):
        record.msg = record.msg.strip()
        return super(BlankFormatter, self).format(record)

class MyLogHandler(logging.StreamHandler):
    def emit(self, record):
        self.format(record)

class IgnoreRequests(logging.Filter):
    # simple example of log message filtering

    def filter(self, record):
        return 'GET /' not in record.getMessage() and 'POST /' not in record.getMessage() and 'DELETE /' not in record.getMessage() and 'PUT /' not in record.getMessage()

class Logger:
    def getLoggerLevel(mode):
        level=logging.DEBUG
        if mode:
            if mode == "INFO":
                level=logging.INFO
            elif mode == "WARNING":
                level=logging.WARNING
            elif mode == "ERROR":
                level=logging.ERROR
            elif mode == "CRITICAL":
                level=logging.CRITICAL
        return level

    def setup(mode, filename):
        headers = [logging.StreamHandler()]
        if filename:
            headers.append(logging.FileHandler(filename))
        format2 = '[%(asctime)s] %(levelname)-11s - %(message)s'
        logging.basicConfig(level=Logger.getLoggerLevel(mode), format=format2, handlers=headers)
