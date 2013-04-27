import collections
import logging

import packet
import serializedobject


logger = logging.getLogger(__name__)

class MessageHeader(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'type'         : serializedobject.uchar,
        'id'           : serializedobject.ushort,
        # first 4 bits: index; last 4 bits: number of parts
        'parts'        : serializedobject.uchar,
        'message_size' : serializedobject.ushort}

    def __init__(self, type = 0, id = 0, size = 0, index = 0, num_parts = 1):
        super(MessageHeader, self).__init__()
        self.type = type
        self.id = id
        self.message_size = size

        if index > 14 or num_parts > 15:
            raise RuntimeError('Can only have 15 parts to a message')

        self.index = index
        self.num_parts = num_parts


    def before_pack(self):
        self.parts = self.index | (self.num_parts << 4)


    def after_unpack(self):
        self.index = self.parts & 0xF
        self.num_parts = (self.parts & 0xF0) >> 4


class _MultipartMessage(object):
    def __init__(self, type, id, addr, length):
        self.type = type
        self.id = id
        self.addr = addr
        self.length = length
        self.parts = length * [None]


class Dispatcher(object):
    RELIABLE_QUEUE_LEN = 32

    def __init__(self, message_types):
        self.reliable_id_queue = collections.deque(maxlen=Dispatcher.RELIABLE_QUEUE_LEN)
        self.newest_reliable_id = packet.MAX_SEQUENCE
        self.pending_reliable_messages = dict()

        self.newest_unreliable_id = packet.MAX_SEQUENCE

        self.message_types = message_types
        self.message_handlers = dict()

        self._multipart_messages = dict()


    def receive(self, data, addr):
        total_length = len(data)
        while len(data) > 0:
            header = MessageHeader()
            data = header.unpack(data)
            payload = data[:header.message_size]
            data = data[header.message_size:]
            if header.num_parts != 1:
                if header.id not in self._multipart_messages:
                    self._multipart_messages[header.id] = _MultipartMessage(
                        header.type, header.id, addr, header.num_parts)
                msg = self._multipart_messages[header.id]
                if header.index < msg.length and msg.addr == addr:
                    msg.parts[header.index] = payload

                    if not any(x == None for x in msg.parts):
                        # we have all parts
                        payload = ''.join(msg.parts)

                        self._process_message(msg.type, msg.id, payload, msg.addr)
                        del self._multipart_messages[header.id]
            else:
                self._process_message(header.type, header.id, payload, addr)


    def _process_message(self, type, id, payload, addr):
        """called after we have a complete message (includes reconstructing
        multipart messages)

        """
        if type in self.message_handlers:
            is_reliable = self.message_types.reliable_map[type]

            if is_reliable:
                if id in self.reliable_id_queue:
                    # duplicate! discard
                    logger.error('discarding message {} (type {}); duplicate'.format(
                            id, self.message_types.to_str(type)))
                    return

                self.reliable_id_queue.append(id)

                if packet.next_sequence(self.newest_reliable_id) == id:
                    self._handle_reliable_msg(type, id, payload, addr)
                    while packet.next_sequence(self.newest_reliable_id) in self.pending_reliable_messages:
                        seq = packet.next_sequence(self.newest_reliable_id)
                        msg = self.pending_reliable_messages[seq]
                        self._handle_reliable_msg(*msg)
                        del self.pending_reliable_messages[seq]
                else:
                    self.pending_reliable_messages[id] = (type, id, payload, addr)
            else:
                allowed_unorderedness = self.message_types.allowed_unorderedness_map[type]
                if allowed_unorderedness >= 0:
                    id = self.newest_unreliable_id
                    for i in range(allowed_unorderedness):
                        id = packet.previous_sequence(id)

                    if packet.sequence_less_than(id, id):
                        # old message! discard
                        type_str = self.message_types.to_str(type)
                        logger.warning('discarding message {} (type {}); older than {}'.format(
                                id, type_str, self.newest_unreliable_id))
                        return

                if not packet.sequence_less_than(id, self.newest_unreliable_id):
                    self.newest_unreliable_id = id
                self.newest_unreliable_id = max(id, self.newest_unreliable_id)
                self.message_handlers[type](id, payload, addr)
        else:
            logger.info('Type {} not registered...dropping message'.
                        format(self.message_types.to_str(type)))


    def _handle_reliable_msg(self, type, id, payload, addr):
        self.message_handlers[type](id, payload, addr)
        self.newest_reliable_id = id



    def register_handler(self, type, fn):
        self.message_handlers[type] = fn
