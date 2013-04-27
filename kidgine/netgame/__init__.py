# exception classes
class InvalidPlayer(Exception):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return 'Invalid player id: {}'.format(self.id)


class InvalidPeer(Exception):
    def __init__(self, addr):
        self.addr = addr

    def __str__(self):
        return 'Invalid peer with {}'.format(self.addr)
