from .. import utils
from ..math import vector
from ..net import serializedobject


tags = utils.enum(*['IMPEEDS_MOVEMENT'])


class Shape(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        '_points' : serializedobject.Array(vector.Vector, 1),
        'rotation': serializedobject.float, } # in radians

    def __init__(self, owner=None):
        self._points = []
        self.owner = owner
        self.tags = set()
        self.rotation = 0.0


    def all_projecting_axes(self, pos_override, shape, shape_override):
        axes = []

        last_point = None
        for point in self._points:
            point = self.transformed_point(point, pos_override)

            if last_point is None:
                last_point = self.transformed_point(self._points[-1], pos_override)

            axis = vector.Vector(last_point.y - point.y, point.x - last_point.x)
            if axis.magnitude_sqr() > 0:
                axis = axis.normalized()
                axes.append(axis)

            last_point = point

        return axes


    def project_onto_axis(self, pos_override, axis):
        min = None
        max = None

        for point in self._points:
            point = self.transformed_point(point, pos_override)
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
