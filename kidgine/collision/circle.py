import shape
from ..math import vector
from ..net import serializedobject


class Circle(shape.Shape):
    _SERIALIZED_MEMBERS = shape.Shape._SERIALIZED_MEMBERS.copy()
    _SERIALIZED_MEMBERS.update({
            'radius' : serializedobject.float })

    def __init__(self, owner=None, position=vector.zero(), radius=1):
        super(Circle, self).__init__(owner)

        self._points = [position]
        self.radius = radius


    def all_projecting_axes(self, pos_override, shape, shape_override):
        center = self.transformed_point(self._points[0], pos_override)

        min_dist_sqr = None
        closest = None
        for point in shape._points:
            point = shape.transformed_point(point, shape_override)

            dist_sqr = point.distance_sqr(center)
            if min_dist_sqr is None or dist_sqr < min_dist_sqr:
                min_dist_sqr = dist_sqr
                closest = point

        return [(closest - center).normalized()]


    def project_onto_axis(self, pos_override, axis):
        center = self.transformed_point(self._points[0], pos_override)

        dot = axis.x * center.x + axis.y * center.y
        return dot - self.radius, dot + self.radius


    def __str__(self):
        pos = self.transformed_point(self._points[0])
        return '<circle at {} of radius {}>'.format(pos, self.radius)
