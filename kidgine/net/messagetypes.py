from .. import utils
import collections

class MessageTypes(object):
    """Represents a list of available message types. A message type
    consists of a name (internally gets mapped to a unique int) and
    whether or not it's reliable. Additionally, for unreliable
    messages, the maximum out-of-orderness allowed is included. If the
    message is out of order in the sequence by more than this amount,
    it is ignored.

    """

    def __init__(self):
        self._message_types = collections.OrderedDict()


    def add_reliable_message_type(self, name):
        self._message_types[name] = (True, 0)
        self._rebuild()


    def add_unreliable_message_type(self, name, max_out_of_orderness):
        self._message_types[name] = (False, max_out_of_orderness)
        self._rebuild()


    def _rebuild(self):
        self.types = utils.enum(*[k for k,v in self._message_types.iteritems()])
        self.reliable_map = [v[0] for k,v in self._message_types.iteritems()]
        self.allowed_unorderedness_map = [v[1] for k,v in self._message_types.iteritems()]

        self._strs = {i : k for (i, (k,v)) in enumerate(self._message_types.iteritems())}


    def to_str(self, type):
        try:
            return self._strs[type]
        except KeyError:
            return str(type)
