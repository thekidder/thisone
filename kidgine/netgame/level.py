import cPickle
import logging


FORMAT=2

logger = logging.getLogger(__name__)


def load(path):
    try:
        with open(path, 'rb') as f:
            obj = cPickle.load(f)
            return obj
    except IOError:
        logger.warning('failed to load from {}'.format(path))
        return None
    except cPickle.UnpicklingError:
        logger.warning('failed to unpickle {}'.format(path))
        return None


def save(level, path):
    try:
        with open(path, 'wb') as f:
            cPickle.dump(level, f, FORMAT)
    except IOError:
        logger.info('failed to save to ' + path)
    finally:
        f.close()

class Level(object):
    def __init__(self):
        self.static_entities = list()
        self.dynamic_entities = list()
