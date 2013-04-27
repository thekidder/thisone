import time

import serializedobject


# 2 ^ 16 - 1
MAX_SEQUENCE = (1 << 16) - 1

class Packet(serializedobject.SerializedObject):
    # format:
    #  protocol version  (4 bytes)
    #  sequence number   (2 bytes)
    #  ack               (2 bytes)
    #  ack bitfield      (4 bytes)
    #  ack received (ms) (2 bytes)
    #  packet sent (ms)  (2 bytes)
    _SERIALIZED_MEMBERS = {
        'version'           : serializedobject.uint,
        'sequence'          : serializedobject.ushort,
        'last_ack'          : serializedobject.ushort,
        'ack_bitfield'      : serializedobject.uint,
        'ack_received_time' : serializedobject.ushort,
        'packet_sent_time'  : serializedobject.ushort}


    def __init__(self, protocol):
        super(Packet, self).__init__()
        self.protocol = protocol


    def before_pack(self):
        self.version = self.protocol.latest_version()

        self.ack_received_time = local_time_to_network_time(self.ack_received_time)
        self.packet_sent_time = local_time_to_network_time(self.packet_sent_time)

        if(len(self.acks) > 0):
            self.last_ack = self.acks[0]
            curr_ack = self.acks[0]
            i = 1

            self.ack_bitfield = 0
            while self.last_ack - curr_ack < 32 and i < len(self.acks):
                curr_ack -= 1
                while i < len(self.acks) and curr_ack < self.acks[i]:
                    i += 1
                if i < len(self.acks) and curr_ack == self.acks[i]:
                    self.ack_bitfield |= (1 << (self.last_ack - curr_ack - 1))
        else:
            # we don't do a good job dealing with non-existent acks...
            # just pretend an ack of 0 indicates no packet to ack
            self.last_ack = 0
            self.ack_bitfield = 0


    def after_unpack(self):
        self.valid = self.protocol.is_valid(self.version)
        self.version = self.protocol.version(self.version)

        self.acks = []
        self.acks.append(self.last_ack)
        for i in range(32):
            bitmask = 1 << i
            if bitmask & self.ack_bitfield > 0:
                self.acks.append(self.acks[0] - i - 1)

        if self.ack_received_time > self.packet_sent_time:
            # not possible for ack to be received before the packet is sent;
            # time must have wrapped. correct for that
            self.packet_sent_time += (1 << 16)


    @staticmethod
    def create_from_data(protocol, data, sequence, acks, ack_received_time):
        p = Packet(protocol)
        p.sequence = sequence
        p.acks = acks
        p.ack_received_time = ack_received_time
        p.packet_sent_time = time.time() # assume now is when the packet is sent
        p.payload = data
        p.data = p.pack() + data
        return p


    @staticmethod
    def create_from_network(protocol, data):
        p = Packet(protocol)
        p.data = data
        data = p.unpack(data)
        p.payload = data
        return p


    def __lt__(self, other):
        if not isinstance(other, Packet):
            return NotImplemented

        return sequence_less_than(self.sequence, other.sequence)


def previous_sequence(s):
    prev = s - 1
    if prev < 0:
        prev = MAX_SEQUENCE

    return prev


def next_sequence(s):
    next = s + 1
    if(next > MAX_SEQUENCE):
        next = 0

    return next


def sequence_less_than(s1, s2):
    return ((s2 > s1) and (s2 - s1 <= MAX_SEQUENCE/2) or
            (s1 > s2) and (s1 - s2 >  MAX_SEQUENCE/2))


def sequence_cmp(s1, s2):
    if sequence_less_than(s1, s2):
        return 1
    elif sequence_less_than(s2, s1):
        return -1
    else:
        return 0


# send timestamp across network in milliseconds as 2-byte integer

def local_time_to_network_time(t):
    t = int(t * 1000)
    return t & 0xffff
