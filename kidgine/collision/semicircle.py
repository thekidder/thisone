import math

from ..net import serializedobject
import shape
from ..math import vector


class Semicircle(shape.Shape):
    _SERIALIZED_MEMBERS = shape.Shape._SERIALIZED_MEMBERS.copy()
    _SERIALIZED_MEMBERS.update({
        'radius'   : serializedobject.float,
        'arc'      : serializedobject.float, }) # in radians

    def __init__(self, owner=None, position=vector.zero(), radius=1, arc=math.pi, rotation=0.):
        super(Semicircle, self).__init__(owner)

        self._points  = [position]
        self.radius   = radius

        if arc > math.pi:
            raise RuntimeError('arc length must be pi or less')

        self.arc      = arc
        self.rotation = rotation


    def all_projecting_axes(self, pos_override, shape, shape_override):


        axes = list()

        min_dist_sqr  = None
        closest_other = None
        closest_mine  = None

        for my_point in self._get_points():
            my_point = self.transformed_point(my_point, pos_override)

            for other_point in shape._get_points():
                other_point = shape.transformed_point(other_point, shape_override)

                dist_sqr = other_point.distance_sqr(my_point)
                if(min_dist_sqr is None or dist_sqr < min_dist_sqr) and dist_sqr > 0:
                    min_dist_sqr = dist_sqr
                    closest_other = other_point
                    closest_mine = my_point

        return [(closest_other - closest_mine).normalized()]


    def project_onto_axis(self, pos_override, axis):
        candidates = list()

        # candidate candidates:

        # center
        candidates.append(self._project(self._points[0], pos_override, axis))
        # endpoints of the semicircle
        direction = self.rotation - self.arc / 2.0
        endpoint = self._points[0] + vector.from_radians(direction) * self.radius
        candidates.append(self._project(endpoint, pos_override, axis))
        direction = self.rotation + self.arc / 2.0
        endpoint = self._points[0] + vector.from_radians(direction) * self.radius
        candidates.append(self._project(endpoint, pos_override, axis))

        # look at bounds of circle and determine if they're in the semicircle
        axis_direction = axis.to_radians()
        if(axis_direction >= self.rotation - self.arc / 2.0 and
           axis_direction <= self.rotation + self.arc / 2.0):
            candidates.append(self._project(self._points[0] + self.radius * axis, pos_override, axis))

        axis_direction = (-axis).to_radians()
        if(axis_direction >= self.rotation - self.arc / 2.0 and
           axis_direction <= self.rotation + self.arc / 2.0):
            candidates.append(self._project(self._points[0] + self.radius * -axis, pos_override, axis))

        return min(candidates), max(candidates)


    def _get_points(self):
        points = list()
        points.append(self._points[0])

        direction = self.rotation - self.arc / 2.0
        import logging
        logger = logging.getLogger(__name__)
        endpoint = self._points[0] + vector.from_radians(direction) * self.radius
        points.append(endpoint)
        direction = self.rotation + self.arc / 2.0
        endpoint = self._points[0] + vector.from_radians(direction) * self.radius
        points.append(endpoint)

        end = self._points[0] + vector.from_radians(self.rotation) * self.radius
        points.append(end)

        return points



    def _project(self, point, override, axis):
        # first transform
        point = self.transformed_point(point, override)
        # then project
        return axis.x * point.x + axis.y * point.y


    def __str__(self):
        pos = self.transformed_point(self._points[0])
        return '<semicircle at {} of radius {}, arc {}, rotation {}>'.format(
            pos, self.radius, self.arc, self.rotation)
