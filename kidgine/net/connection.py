import collections
import logging
import time

import flowcontrol
import packet
from .. import utils


logger = logging.getLogger(__name__)

# enum for connection status.
# a connection follows linearly through the following three states throughout its lifetime.
# it cannot transition from disconnected -> initializing; recreate the connection with
# the same peer info if the connection unexpectedly drops
ConnectionStatus = utils.enum(
    INIT='initializing',
    CONNECTED='connected',
    DISCONNECTED='disconnected')

class Connection(object):
    RTT_FILTER_FACTOR = 0.1
    TIMEOUT = 5.0

    def __init__(self, protocol, socket, peer):
        """initialize a connection manager with peer, communicating over socket"""
        self.protocol = protocol

        self.sequence = 0
        self.socket = socket
        self.peer = peer

        # last packet received. using UDP, so not necessarily the packet with
        # the highest sequence number
        self.last_packet = None
        self.last_packet_send_time = 0
        # connection is defined as valid ack received less than TIMEOUT ago
        self.last_packet_acked_time = time.time()
        self.last_received_sequences = list()
        self.packet_times = dict()

        # RTT in milliseconds, calculated with low-pass filter
        # this is total RTT, including time on the other end
        self.rtt = 50
        # last packet RTT
        self.last_rtt = 0
        # network RTT - does not include time spent on the other end
        self.net_rtt = 50
        self.net_last_rtt = 0
        # total packets sent
        self.packets_sent = 0
        # total packets acknowledged by the other end
        self.packets_acked = 0
        # total packets received
        self.packets_received = 0
        # total packets lost. packet loss % is packets_lost / packets_sent
        self.packets_lost = 0

        # average bytes/sec received over the last 64 packets
        self.avg_received_size = 0
        # last received packet size
        self.last_received_size = 0
        # average bytes/sec sent over the last 64 packets
        self.avg_sent_size = 0
        # last sent packet size
        self.last_sent_size = 0

        self.connected = ConnectionStatus.INIT

        # set up some hidden state
        # objects to notify on connect/disconnect
        self._callbacks = list()
        # mapping of sequence, data of packets that must be delivered reliably
        self._reliable_packets = dict()
        # queues to keep track of packet size
        self._sent_size_queue     = collections.deque(maxlen=64)
        self._received_size_queue = collections.deque(maxlen=64)


    def register_callbacks(self, object):
        """object should implement on_connect and on_disconnect
        both have a signature of on_[dis]connect(addr)

        """
        self._callbacks.append(object)


    def send_data(self, data):
        p = packet.Packet.create_from_data(
            self.protocol,
            data,
            self.sequence,
            self.last_received_sequences,
            self.last_packet_acked_time)

        self._sent_size_queue.append((time.time(), len(p.data)))
        self.last_sent_size = len(p.data)

        self.packets_sent += 1

        self.packet_times[self.sequence] = time.time()
        sent_sequence = self.sequence
        self.last_packet_send_time = time.time()
        self.socket.sendto(p.data, self.peer)
        self.sequence = packet.next_sequence(self.sequence)

        return sent_sequence


    def send_data_reliable(self, data):
        """attempts to send data, and resends it when we detect it is lost.
        note that no effort is made to disambiguate the same packet received
        two or more times - applications should keep track of this. we may also
        send the packet multiple times to begin with to minimize latency and guarantee
        packet arrival. tl;dr: for reliable data, include a message ID so we only
        process it on the receiving end once.

        """
        sequence = self.send_data(data)
        self._reliable_packets[sequence] = data


    def receive_data(self, peer, data):
        if not peer == self.peer:
            raise Exception("This packet is not from the correct peer: (got " + \
                                str(peer) + "; expected " + str(self.peer) + ")")
        p = packet.Packet.create_from_network(self.protocol, data)

        num_acks = len(self.last_received_sequences)
        if num_acks > 0:
            last_known_sequence = self.last_received_sequences[num_acks-1]
            if packet.sequence_less_than(p.sequence, last_known_sequence) \
                    and self.connected == ConnectionStatus.CONNECTED:
                # packet is too old or sequence is very garbled; drop it on the floor
                print 'Dropping packet {} (first ack {}; last ack {})'.format(
                    p.sequence,
                    self.last_received_sequences[num_acks-1],
                    self.last_received_sequences[0])
                return None

        # only measure received size after we accept it
        self._received_size_queue.append((time.time(), len(p.data)))
        self.last_received_size = len(p.data)

        self.packets_received += 1
        self.last_packet = p

        # look at acks the other end has sent us and use to calculate RTT
        for ack in p.acks:
            if ack in self.packet_times:
                start_time = self.packet_times[ack]

                del self.packet_times[ack]

                # update RTTs
                new_rtt = time.time() - start_time
                new_rtt *= 1000.0 # convert to milliseconds
                self.rtt = _low_pass_filter(
                    Connection.RTT_FILTER_FACTOR, self.rtt, new_rtt)
                self.last_rtt = new_rtt

                net_new_rtt = int(new_rtt) - (p.packet_sent_time - p.ack_received_time)

                if net_new_rtt < 0:
                    net_new_rtt = 0 # negative packet time! unpossible!

                self.net_rtt = _low_pass_filter(
                    Connection.RTT_FILTER_FACTOR, self.net_rtt, net_new_rtt)
                self.net_last_rtt = net_new_rtt

                self.packets_acked += 1
                self.last_packet_acked_time = time.time()

                # is this reliable? we can delete from dict
                if ack in self._reliable_packets:
                    del self._reliable_packets[ack]

                # clear all stats on a new connection
                if self.connected != ConnectionStatus.CONNECTED:
                    self.packet_times = dict()
                    self.last_received_sequences = list()

                    self.packets_sent = 0
                    self.packets_received = 0
                    self.packets_acked = 0
                    self.packets_lost = 0

                    self.connected = ConnectionStatus.CONNECTED

                    # init flow control
                    self.flowcontrol = flowcontrol.BinaryFlowControl()

                    for c in self._callbacks:
                        c.on_connect(self.peer)

        # keep track of packets we've received to ack back to the other end
        self.last_received_sequences.insert(0, p.sequence)
        if self.connected == ConnectionStatus.CONNECTED:
            # if we are connected, keep the highest 33 packet sequences we
            # have received. However, if we are trying to connect, don't sort:
            # this results in the _last_ 33 packets being kept. This aids in
            # starting a connection before we know exactly where in the remote
            # sequence a client is
            self.last_received_sequences = sorted(
                self.last_received_sequences, packet.sequence_cmp)

        self.last_received_sequences = self.last_received_sequences[:33]

        # return packet to caller
        return p


    def update(self):
        """call once per frame to do cleanup and update state"""
        self.cleanup_rtts()

        if len(self._sent_size_queue) > 1:
            # update packet sizes
            sent_time_window = self._sent_size_queue[-1][0] - self._sent_size_queue[0][0]
            self.avg_sent_size = 0
            for t,length in self._sent_size_queue:
                self.avg_sent_size += length
            self.avg_sent_size /= sent_time_window

        if len(self._received_size_queue) > 1:
            received_time_window = self._received_size_queue[-1][0] - self._received_size_queue[0][0]
            self.avg_received_size = 0
            for t,length in self._received_size_queue:
                self.avg_received_size += length
            self.avg_received_size /= received_time_window

        if self.connected == ConnectionStatus.CONNECTED:
            self.flowcontrol.update(self.net_rtt, time.time() - self.last_packet_acked_time)
            if time.time() - self.last_packet_acked_time > Connection.TIMEOUT:
                self.disconnect()

        if self.connected != ConnectionStatus.DISCONNECTED:
            # send a heartbeat packet
            # the function is only to establish that we are connected
            # and everything is working properly - no data is necessary
            if time.time() - self.last_packet_send_time > flowcontrol.HEARTBEAT_TIME:
                self.send_data('')


    def disconnect(self):
        self.connected = ConnectionStatus.DISCONNECTED
        self.last_received_sequences = list()
        self.packet_times = dict()

        for c in self._callbacks:
            c.on_disconnect(self.peer)


    def cleanup_rtts(self):
        curr_time = time.time()
        for sequence, t in self.packet_times.items():
            dt = (curr_time - t) * 1000.0
            if dt > 1000.0:
                del self.packet_times[sequence]
                self.packets_lost += 1

                # is this reliable? need to resend and update state
                if sequence in self._reliable_packets:
                    data = self._reliable_packets[sequence]
                    del self._reliable_packets[sequence]
                    new_sequence = self.send_data(data)
                    self._reliable_packets[new_sequence] = data


    def format_connection_stats(self):
        if self.packets_sent == 0:
            loss_percent = 0
        else:
            loss_percent = float(self.packets_lost) / self.packets_sent * 100.0

        time_since_packet = time.time() - self.last_packet_acked_time

        bad_mode = ''
        if not self.flowcontrol.good:
            bad_mode = '(BAD MODE)'

        str = 'Connection with {} ({}) {}:\n \
\ttime since last packet: {:.2f}\n \
\tRTT (ms):     {:5.1f}/{:5.1f}, Net RTT (ms):    {:5.1f}/{:5.1f}\n \
\tsent size:    {:4d}/{:6.1f}, recv size:       {:4d}/{:6.1f}\n \
\tpackets sent: {:11d}, packets received: {:10d}\n \
\tpackets acked:{:11d}, packets lost:     {:10d} ({:.2f}%)'.format(
    self.peer, self.connected, bad_mode,
    time_since_packet,
    self.last_rtt, self.rtt, self.net_last_rtt, self.net_rtt,
    self.last_sent_size, self.avg_sent_size, self.last_received_size, self.avg_received_size,
    self.packets_sent, self.packets_received,
    self.packets_acked, self.packets_lost, loss_percent)

        return str


    def print_connection_stats(self, level):
        logger.log(level, self.format_connection_stats())


def _low_pass_filter(rate, old, new):
    return rate * new + (1.0 - rate) * old
