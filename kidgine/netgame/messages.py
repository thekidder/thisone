import gamestate
from ..net import serializedobject, messagetypes


default_messages = messagetypes.MessageTypes()
# client commands
default_messages.add_reliable_message_type('SET_SVAR')
default_messages.add_reliable_message_type('LOAD_LEVEL')

# server updates
default_messages.add_reliable_message_type('INIT_LEVEL')
default_messages.add_reliable_message_type('SVAR_UPDATE')
default_messages.add_reliable_message_type('INVALID_CMD')

# client input commands
default_messages.add_unreliable_message_type('INPUT_COMMAND',     -1)

# server updates - unreliable
default_messages.add_unreliable_message_type('GAMESTATE_UPDATE',   0)
default_messages.add_unreliable_message_type('TIMESTAMP',          0)


# used both for SET_SVAR and UPDATE_SVAR
class _SetSvarMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'name'  : serializedobject.String(255),
        'value' : serializedobject.String(255) }

    def __init__(self, name = '', value = ''):
        super(_SetSvarMsg, self).__init__()
        self.set(name, value)


    def set(self, name, value):
        self.name = name
        self.value = value

        return self


SetSvarMsg = _SetSvarMsg()


class _LoadLevelMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'name'  : serializedobject.String(255) }

    def __init__(self, name = ''):
        super(_LoadLevelMsg, self).__init__()
        self.set(name)


    def set(self, name):
        self.name = name

        return self


LoadLevelMsg = _LoadLevelMsg()


class _InvalidCmdMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'message'  : serializedobject.String(255) }

    def __init__(self, message = ''):
        super(_InvalidCmdMsg, self).__init__()
        self.set(message)


    def set(self, message):
        self.message = message

        return self


InvalidCmdMsg = _InvalidCmdMsg()


class _TimestampMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'timestamp' : serializedobject.float}

    def __init__(self, time=0):
        super(_TimestampMsg, self).__init__()
        self.set(time)


    def set(self, time):
        self.timestamp = time

        return self


TimestampMsg = _TimestampMsg()


class _GamestateUpdateMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'last_input_ack' : serializedobject.uint,
        'state'          : gamestate.DynamicGamestate,
        'life_msgs'      : gamestate.LifeMessages }

    def __init__(self, ack_id=0, state=None, life_msgs=None):
        super(_GamestateUpdateMsg, self).__init__()
        self.set(ack_id, state, life_msgs)


    def set(self, ack_id, state, life_msgs):
        self.last_input_ack = ack_id
        self.state = state
        self.life_msgs = life_msgs

        return self


GamestateUpdateMsg = _GamestateUpdateMsg()


class _InitLevelMsg(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'level_path' : serializedobject.String(255),
        'player_id'  : serializedobject.uint }

    def __init__(self, player_id=0, level_path=''):
        super(_InitLevelMsg, self).__init__()
        self.set(player_id, level_path)


    def set(self, player_id, level_path):
        self.player_id = player_id
        self.level_path = level_path

        return self


InitLevelMsg = _InitLevelMsg()
