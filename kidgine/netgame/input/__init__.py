from ...net import serializedobject
from ...math import clamp

class InputState(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'duration_ms' : serializedobject.uchar }

    def __init__(self):
        pass


    def set_duration(self, duration):
        self.duration = duration


    def before_pack(self):
        self.duration_ms = int(self.duration * 1000.0)
        self.duration_ms = clamp(self.duration_ms, 0, 255)


    def after_unpack(self):
        self.duration = self.duration_ms / 1000.0
