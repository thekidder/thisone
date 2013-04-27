import select
import socket

import connection
import dispatcher
import logging
import sender


logger = logging.getLogger(__name__)

class _Peer(object):
    def __init__(self, protocol, message_types, socket, addr):
        self.connection = connection.Connection(protocol, socket, addr)
        self.sender = sender.Sender(self.connection, message_types)
        self.dispatcher = dispatcher.Dispatcher(message_types)


    def update(self):
        self.connection.update()



class NetworkManager:
    def __init__(self, protocol, message_types, addr = None):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        if addr is not None:
            self._socket.bind(addr)
            logger.info('Bound to ' + str(self._socket.getsockname()))

        self._all_peers = dict()

        self._connection_callbacks = list()
        self._receive_handlers = dict()

        self._protocol = protocol
        self._message_types = message_types


    def _add_peer(self, addr):
        if addr in self._all_peers:
            return

        logger.info('connecting to ' + str(addr))
        self._all_peers[addr] = _Peer(self._protocol, self._message_types, self._socket, addr)
        self._all_peers[addr].connection.register_callbacks(self)
        # register all receive callbacks
        for type,fn in self._receive_handlers.iteritems():
            self._all_peers[addr].dispatcher.register_handler(type, fn)


    def _get_peer(self, addr):
        if addr not in self._all_peers:
            raise RuntimeError('Trying to send packet to unknown peer!')

        peer = self._all_peers[addr]
        if peer.connection.connected != connection.ConnectionStatus.CONNECTED:
            raise RuntimeError('Trying to send packet to unconnected peer!')

        return peer


    def get_connection(self, addr):
        return self._get_peer(addr).connection


    def connected_peers(self):
        for addr,peer in self._all_peers.iteritems():
            if peer.connection.connected == connection.ConnectionStatus.CONNECTED:
                yield addr


    def connect(self, addr):
        self._add_peer(addr)


    def broadcast(self, type, data):
        for addr in self.connected_peers():
            self.send_immediate(addr, type, data)


    def send_immediate(self, addr, type, data):
        peer = self._get_peer(addr)
        return peer.sender.send_immediate(type, data)


    def queue(self, addr, type, data):
        peer = self._get_peer(addr)
        return peer.sender.queue(type, data)


    def send_all(self, addr):
        peer = self._get_peer(addr)
        peer.sender.send_all()


    def register_connection_callbacks(self, object):
        self._connection_callbacks.append(object)


    def register_receive_handler(self, type, fn):
        self._receive_handlers[type] = fn
        for peer in self._all_peers.values():
            peer.dispatcher.register_handler(type, fn)


    def update(self):
        """call once a frame to process all waiting packets and do all updates"""
        read_ready, _, __ = select.select([self._socket], [], [], 0)
        while read_ready:
            try:
                data, addr = self._socket.recvfrom(2048)
            except socket.error:
                break # probably got a WSACONNRESET error on windows; exit out of update
            else:
                # new peer, set up data structures
                if addr not in self._all_peers:
                    self._add_peer(addr)

                response = self._all_peers[addr].connection.receive_data(addr, data)
                if response is not None:
                    self._all_peers[addr].dispatcher.receive(response.payload, addr)
                else:
                    logger.error('Received bad packet from ' + str(addr))

                read_ready, _, __ = select.select([self._socket], [], [], 0)

        # update all connections
        for peer in self._all_peers.values():
            peer.connection.update()


    # internal callbacks
    def on_connect(self, addr):
        for o in self._connection_callbacks:
            o.on_connect(addr)


    def on_disconnect(self, addr):
        for o in self._connection_callbacks:
            o.on_disconnect(addr)
        del self._all_peers[addr]
