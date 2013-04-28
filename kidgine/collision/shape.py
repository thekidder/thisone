from .. import utils
from ..math import vector
from ..net import serializedobject


tags = utils.enum(*['IMPEEDS_MOVEMENT'])


class Shape(object):#serializedobject.SerializedObject):
#    _SERIALIZED_MEMBERS = {
#        '_points' : serializedobject.Array(vector.Vector, 1),
#        'rotation': serializedobject.float, } # in radians

    def __init__(self, owner=None):
        self._points = list()
        self._transformed_points = list()
        self._cached_axes = list()
        self.owner = owner
        self.tags = set()
        self.rotation = 0.0


    def all_projecting_axes(self, pos_override, shape, shape_override, calculate = False):
        if pos_override is None and not calculate:
            return self._cached_axes
        axes = []

        last_point = None
        for point in self._all(pos_override):
            if last_point is None:
                if pos_override is None:
                    last_point = self._transformed_points[-1]
                else:
                    last_point = self.transformed_point(self._points[-1], pos_override)

            axis = vector.Vector(last_point.y - point.y, point.x - last_point.x)
            if axis.magnitude_sqr() > 0:
                axis = axis.normalized()
                axes.append(axis)

            last_point = point

        return axes


    def update(self):
        del self._transformed_points[0:len(self._transformed_points)]
        for p in self._points:
            self._transformed_points.append(self.transformed_point(p))

        self._cached_axes = self.all_projecting_axes(None, None, None, calculate = True)


    def _all(self, pos_override):
        if pos_override:
            for p in self._points:
                yield self.transformed_point(p, pos_override)
        else:
            for p in self._transformed_points:
                yield p


    def project_onto_axis(self, pos_override, axis):
        min = None
        max = None

        for point in self._all(pos_override):
            dot = axis.x * point.x + axis.y * point.y
            if min is None or dot < min:
                min = dot
            if max is None or dot > max:
                max = dot

        return min, max


    def _get_points(self):
        """some shapes use the points of another to determine their
        projecting axes. by default this just the list of points a
        shape has; others (semicircles) define this slightly
        differently"""
        return self._points

    def transformed_point(self, p, override = None):
        if self.rotation != 0:
            p = p.rotate(self.rotation)

        center = vector.constant_zero
        if override is not None:
            center = override
        elif self.owner is not None:
            center = self.owner.position
        elif self.center is not None:
            center = self.center

        return p + center
