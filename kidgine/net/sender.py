import logging

import dispatcher
import packet


logger = logging.getLogger(__name__)

class Sender(object):
    def __init__(self, connection, message_types):
        self.connection = connection
        # monotonically increasing sequence number for message id.
        # two byte, wrapping sequence (exactly the same as packet sequence)
        self.unreliable_id = 0
        self.reliable_id = 0
        # never send reliable and unreliable messages in the same packet
        # keep two separate lists to disambiguate
        self.message_queue = []
        self.reliable_message_queue = []

        self.message_types = message_types

        # maximum size for bundling packets
        self.MAXIMUM_PACKET_SIZE = 1400 - packet.Packet.static_size


    def queue(self, type, data):
        is_reliable = self.message_types.reliable_map[type]

        if is_reliable:
            list_to_append = self.reliable_message_queue
        else:
            list_to_append = self.message_queue

        sent_id = self._get_next_id(is_reliable)
        packets = self._build_packets(type, sent_id, data)

        for p in packets:
            if len(p) > self.MAXIMUM_PACKET_SIZE:
                raise RuntimeError("Message is too large!")

            list_to_append.append(p)

        return sent_id


    def send_immediate(self, type, data):
        is_reliable = self.message_types.reliable_map[type]

        sent_id = self._get_next_id(is_reliable)
        packets = self._build_packets(type, sent_id, data)

        for p in packets:
            if len(p) > self.MAXIMUM_PACKET_SIZE:
                raise RuntimeError("Message is too large!")

            if is_reliable:
                self.connection.send_data_reliable(p)
            else:
                self.connection.send_data(p)

        return sent_id


    def _build_packets(self, type, id, data):
        """Take a string of data and pack into n chunks, where each fits into
        one UDP packet. Return these in a list

        """
        packets = list()

        chunk_size = self.MAXIMUM_PACKET_SIZE - dispatcher.MessageHeader().static_size
        num_chunks = (len(data) + chunk_size - 1) / chunk_size
        for i, chunk in enumerate(_chunks(data, chunk_size)):
            header = dispatcher.MessageHeader(type, id, len(chunk), i, num_chunks)
            packets.append(header.pack() + chunk)

        return packets


    def _get_next_id(self, is_reliable):
        if is_reliable:
            sent_id = self.reliable_id
            self.reliable_id = packet.next_sequence(self.reliable_id)
        else:
            sent_id = self.unreliable_id
            self.unreliable_id = packet.next_sequence(self.unreliable_id)

        return sent_id


    def send_all(self):
        for packet in self._bundle_packets(self.message_queue):
            if len(packet) > 0:
                self.connection.send_data(packet)
        for packet in self._bundle_packets(self.reliable_message_queue):
            if len(packet) > 0:
                self.connection.send_data_reliable(packet)
        self.message_queue = []
        self.reliable_message_queue = []


    def _bundle_packets(self, messages_list):
        total_length = 0
        packet = ''

        for message in messages_list:
            if total_length + len(message) > self.MAXIMUM_PACKET_SIZE:
                final_message = packet
                packet = ''
                total_length = 0
                yield final_message

            total_length += len(message)
            packet += message

        yield packet


def _chunks(l, n):
    """Yield successive n-sized chunks from l.

    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
