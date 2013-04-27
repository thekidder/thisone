import math
import operator

from ..net import serializedobject


class Vector(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'x' : serializedobject.float,
        'y' : serializedobject.float}

    def __init__(self, x=0., y=0.):
        super(Vector, self).__init__()
        self.x = x
        self.y = y

    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)


    def magnitude_sqr(self):
        return self.x * self.x + self.y * self.y


    def _do_operation(self, operator, x):
        if hasattr(x, 'x'):
            return Vector(operator(self.x, x.x), operator(self.y, x.y))
        else:
            return Vector(operator(self.x, x), operator(self.y, x))


    def __add__(self, x):
        return self._do_operation(operator.add, x)

    __radd__ = __add__


    def __sub__(self, x):
        return self._do_operation(operator.sub, x)

    __rsub__ = __sub__


    def __div__(self, x):
        return self._do_operation(operator.div, x)

    __rdiv__ = __div__


    def __mul__(self, x):
        return self._do_operation(operator.mul, x)

    __rmul__ = __mul__


    def __neg__(self):
        return Vector(-self.x, -self.y)


    def __eq__(self, other):
        try:
            return self.x == other.x and self.y == other.y
        except AttributeError:
            return False


    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"


    def distance_sqr(self, v):
        d = self - v
        return d.x * d.x + d.y * d.y


    def distance(self, v):
        return math.sqrt(self.distance_sqr(v))


    def normalized(self):
        mag = self.magnitude()
        if mag == 0.0:
            return zero()
        return Vector(self.x / mag, self.y / mag)


    def to_radians(self):
        return math.atan2(self.y, self.x)


    def rotate(self, angle):
        """roates the current vector around the origin by angle
        radians and return the result"""
        return Vector(self.x * math.cos(angle) - self.y * math.sin(angle),
                      self.x * math.sin(angle) + self.y * math.cos(angle))


    def copy(self):
        return Vector(self.x, self.y)


    def closer_than(self, v, dist):
        return self.distance_sqr(v) < (dist * dist)


    def shorter_than(self, mag):
        return self.magnitude_sqr() < (mag * mag)



def zero():
    return Vector()


def one():
    return Vector(1., 1.)


def right():
    return Vector(1., 0.)


def up():
    return Vector(0., 1.)


constant_zero  = zero()
constant_right = right()
constant_up    = up()


def from_radians(direction):
    """takes a direction in radians"""
    return Vector(math.cos(direction), math.sin(direction))


def interpolate(one, two, interp_time):
    return Vector(
        one.x * (1.0 - interp_time) + two.x * interp_time,
        one.y * (1.0 - interp_time) + two.y * interp_time)
