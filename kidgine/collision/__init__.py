import logging

import shape
from ..math import vector


logger = logging.getLogger(__name__)

DEBUG = False

class CollisionInfo(object):
    def __init__(self, distance, translation_vector, shape1, shape2):
        self.distance = distance
        self.translation_vector = translation_vector
        self.shape1 = shape1
        self.shape2 = shape2


def collides(shape1, shape2, shape1_pos=None, shape2_pos=None):
    all_axes = (shape1.all_projecting_axes(shape1_pos, shape2, shape2_pos) +
                shape2.all_projecting_axes(shape2_pos, shape1, shape1_pos))

    min_distance = None
    min_translation_vector = None

    for axis in all_axes:
        min_a, max_a = shape1.project_onto_axis(shape1_pos, axis)
        min_b, max_b = shape2.project_onto_axis(shape2_pos, axis)

        dist, mult = _overlap(min_a, max_a, min_b, max_b)
        translation_vector = None
        if dist > 0:
            if min_distance is None or dist < min_distance:
                min_distance = dist
                min_translation_vector = axis * dist * mult
        else:
            return None

    return CollisionInfo(min_distance, -min_translation_vector, shape1, shape2)


def _overlap(min_a, max_a, min_b, max_b):
    if(min_a < min_b):
        return -(min_b - max_a), 1
    else:
        return -(min_a - max_b), -1



class SpatialHash(object):
    GRID_SIZE = 128 # must not be smaller than the largest collidable

    @staticmethod
    def _hash_func(position):
        return (int(position.x / SpatialHash.GRID_SIZE), int(position.y / SpatialHash.GRID_SIZE))

    class _Info:
        def __init__(self, collidable, new_pos=None):
            if new_pos is None:
                new_pos = collidable.transformed_point(vector.constant_zero)

            self.collidable = collidable
            self.index = SpatialHash._hash_func(new_pos)


    def __init__(self):
        self.collidables = dict()
        self.hash = dict()


    def clear(self):
        """remove ALL collidables"""
        self.collidables.clear()
        self.hash.clear()


    def get(self, token):
        return self.collidables[token].collidable


    def update(self, token, collidable):
        if token in self.collidables:
            old = self.collidables[token]
            del self.hash[old.index][token]

        info = SpatialHash._Info(collidable)
        if info.index not in self.hash:
            self.hash[info.index] = dict()
        self.collidables[token] = info
        self.hash[info.index][token] = info


    def remove(self, token):
        del self.hash[self.collidables[token].index][token]
        del self.collidables[token]


    def potential_collidables(self, token=None, collidable=None, new_pos=None):
        if token is not None and collidable is not None:
            raise RuntimeError('may pass in token or collidable but not both')

        if new_pos is None:
            if token is not None:
                info = self.collidables[token]
                index = info.index
            elif collidable is not None:
                pos = collidable.owner.position
                index = SpatialHash._hash_func(pos)
            else:
                raise RuntimeError('need a token or collidable')
        else:
            index = SpatialHash._hash_func(new_pos)

        # grab this grid cell and the surrounding nine to check for collidables
        potential_indices = (
            index,
            (index[0] - 1, index[1] - 1),
            (index[0] - 1, index[1]    ),
            (index[0] - 1, index[1] + 1),
            (index[0] + 1, index[1] - 1),
            (index[0] + 1, index[1]    ),
            (index[0] + 1, index[1] + 1),
            (index[0],     index[1] - 1),
            (index[0],     index[1] + 1),
        )

        for index in potential_indices:
            if index in self.hash:
                for token, info in self.hash[index].iteritems():
                    yield token,info.collidable


class CollisionDetector(object):
    def __init__(self):
        self.can_move_filters = set([shape.tags.IMPEEDS_MOVEMENT])

        self.spatial_hash = SpatialHash()
        self.start_frame()


    def start_frame(self):
        """reset stats; run each frame"""
        self.num_checks = 0
        self.broad_phase_checks = 0
        self.narrow_phase_checks = 0


    def log_stats(self, level):
        broad = 0.0
        narrow = 0.0

        if self.num_checks:
            broad = 1.0 * self.broad_phase_checks / self.num_checks
            narrow = 1.0 * self.narrow_phase_checks / self.num_checks

        logger.log(level, '-----------COLLISION DETECTOR-----------')
        stats1 = '\t {:4d} collision checks; avg. {:6.1f} broad phase checks and {:6.1f} narrow phase checks'
        stats2 = '\t                       total {:6d} broad phase checks and {:6d} narrow phase checks'
        logger.log(level, stats1.format(self.num_checks, broad, narrow))
        logger.log(level, stats2.format(self.broad_phase_checks, self.narrow_phase_checks))


    def clear(self):
        """remove ALL collidables"""
        self.spatial_hash.clear()


    def update_collidable(self, token, collidable):
        self.spatial_hash.update(token, collidable)


    def remove_collidable(self, token):
        self.spatial_hash.remove(token)


    def collides(self, token=None, collidable=None, position=None, filters=set()):
        """position overrides the existing collidable position for the
        purposes of this check"""
        self.num_checks += 1
        potential_collidables = self._broad_phase(
            token=token, collidable=collidable, new_pos=position, filters=filters)
        return self._narrow_phase(
            token=token, collidable=collidable, new_pos=position, collidable_list=potential_collidables)


    def can_move_to(self, token, new_pos):
        self.num_checks += 1

        collidable = self.spatial_hash.get(token)

        potential_collidables = self._broad_phase(
            token=token, new_pos=new_pos, filters=self.can_move_filters)

        collision = None
        candidate = new_pos
        final_translation = vector.zero()

        for i in range(3): # maximum number of iterations before we give up
            collision_info = self._narrow_phase(
                collidable=collidable, new_pos=candidate, collidable_list=potential_collidables)

            if collision_info is not None:
                final_translation = final_translation + collision_info.translation_vector
                candidate = new_pos + final_translation
            else:
                break

            collision = collision_info

        if collision is not None:
            collision.translation_vector = final_translation

        return collision


    def _broad_phase(self, token=None, collidable=None, new_pos=None, filters=None):
        """return a list of potentially-colliding objects"""

        if new_pos is None:
            if collidable is not None:
                new_pos = collidable.owner.position
            elif token is not None:
                new_pos = self.spatial_hash.get(token).owner.position

        all = list()
        potential = self.spatial_hash.potential_collidables(
            token=token, collidable=collidable, new_pos=new_pos)

        if collidable is None:
            collidable = self.spatial_hash.get(token)

        for t,shape in potential:
            if token == t:
                continue

            if collidable.owner == shape.owner:
                continue

            if not filters.issubset(shape.tags):
                continue

            self.broad_phase_checks += 1

            if(shape.owner.position.closer_than(new_pos, 2 * SpatialHash.GRID_SIZE)):
                all.append((t,shape))

        return all


    def _narrow_phase(self, token=None, collidable=None, new_pos=None, collidable_list=None):
        if collidable is None:
            collidable = self.spatial_hash.get(token)

        self.narrow_phase_checks += len(collidable_list)
        for t,shape in collidable_list:
            if token == t:
                continue

            collision_info = collides(collidable, shape, new_pos)
            if collision_info is not None:
                return collision_info

        return None
