import logging
import os
import socket

import level


logger = logging.getLogger(__name__)


class DownloadClient(object):
    def __init__(self, addr, name, handler, callback):
        self.addr = addr
        self.name = name
        self.handler = handler
        self.callback = callback


    def download_level(self):
        size = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info('connecting to {}'.format(self.addr))
        try:
            sock.connect(self.addr)
            logger.info('connected; requesting {}'.format(self.name))
            sock.sendall(self.name)
            with open(self.name, 'wb') as f:
                recv_size = 1024
                while True:
                    response = sock.recv(recv_size)
                    size += len(response)
                    if not response:
                        break
                    f.write(response)
        except IOError:
            logger.exception('failed to read from remote')
        finally:
            sock.close()

        level_obj = level.load(self.name)
        if level_obj:
            logger.info('Got {}; size {} bytes'.format(self.name, size))
            def cmd():
                self.callback(level_obj)
            self.handler.put(cmd)
        else:
            logger.warning('Tried to download {} but failed (got {} bytes)'.format(self.name, size))
            os.remove(self.name)
