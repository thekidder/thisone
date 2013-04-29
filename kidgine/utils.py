import logging


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


# log to a file
_fh = None

def _log_file_name(app_name, role):
    suffix = role
    dir = '.'

    return '{}/{}_{}.log'.format(dir, app_name, suffix)


def add_file_logger(app_name, role):
    global _fh
    logger = logging.getLogger()

    log_name = _log_file_name(app_name, role)
    _fh = logging.FileHandler(log_name, 'w')
    logger.addHandler(_fh)
    return log_name


def remove_file_logger():
    if _fh is not None:
        logger = logging.getLogger()

        logger.removeHandler(_fh)
        _fh.close()


def lerp(t, start, end):
    return t * (end - start) + start
