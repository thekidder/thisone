import SocketServer
import logging
import threading

import level


logger = logging.getLogger(__name__)


class ThreadingTcpServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, addr, handler):
        self.allow_reuse_address = True
        # SocketServer classes are not new style. what is this madness?
        SocketServer.TCPServer.__init__(self, addr, handler)


class DownloadServer(object):
    """Creates a server that handles incoming requests for map downloads
    indefinitely. Runs the main listen socket on a new thread, and each
    connection on its own thread as well."""
    class RequestHandler(SocketServer.BaseRequestHandler):
        def setup(self):
            logger.info('download server got connection from {}'.format(
                self.request.getpeername()))

        def handle(self):
            self.server.server._handle(self.request)


    def __init__(self, addr):
        self.server = ThreadingTcpServer(addr, self.RequestHandler)
        self.server.server = self

        self.server_thread = threading.Thread(target = self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info('Started download server at {} running in {}'.format(
            self.server.server_address, self.server_thread.name))


    def _handle(self, request):
        level_name = request.recv(1024).strip()
        logger.info('Received download request for {} from {}.'.format(
            level_name, request.getpeername()))
        if self._is_valid_level(level_name):
            logger.info('sending level')
            with open(level_name, 'rb') as f:
                chunk_size = 1024
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    request.sendall(chunk)


    def _is_valid_level(self, name):
        return level.load(name) is not None
