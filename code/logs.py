
import logging

class Logs:

    logger = None

    def __new__(cls):
        if cls.logger == None:
            # create logger with 'spam_application'
            cls.logger = logging.getLogger('SimpDeDup')
            cls.logger.setLevel(logging.INFO)
            # create file handler which logs even debug messages
            fh = logging.FileHandler('spam.log')
            fh.setLevel(logging.DEBUG)
            # create console handler with a higher log level
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            # create formatter and add it to the handlers
            # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            formatter = logging.Formatter('{asctime} {levelname} {filename}:{funcName}:{lineno} {message}', style='{')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            # add the handlers to the logger
            # logger.addHandler(fh)
            cls.logger.addHandler(ch)
        return cls.logger