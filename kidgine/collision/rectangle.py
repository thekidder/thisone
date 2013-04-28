import shape
from ..math import vector


class Rectangle(shape.Shape):
#    _SERIALIZED_MEMBERS = shape.Shape._SERIALIZED_MEMBERS

    def __init__(self, owner, tl, br, center = None):
        super(Rectangle, self).__init__(owner)

        top_left     = vector.Vector(tl.x, tl.y)
        top_right    = vector.Vector(br.x, tl.y)
        bottom_left  = vector.Vector(tl.x, br.y)
        bottom_right = vector.Vector(br.x, br.y)

        self._points = [top_left, top_right, bottom_right, bottom_left]

        if center is not None:
            self.center = center
