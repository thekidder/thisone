import logging

import kidgine.collision.rectangle
import renderable
from collision import Tags
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

class Ability(object):
    def __init__(self, ability_type, recharge_time):
        self.ability_type = ability_type
        self.recharge_time = recharge_time
        self.last_activation = 0


    def activate(self, t, dt, collision_detector, parent, new_objs):
        if t - self.last_activation > self.recharge_time:
            self.last_activation = t

            new_objs.append(self.ability_type(parent, collision_detector))


class Firebolt(object):
    filter = set([Tags.ENEMY])
    damage = 80 # per second

    def __init__(self, parent, collision_detector):
        self.time_left = 0.2
        self.position = parent.position

        self.token = 'firebolt'

        tl = Vector(-48, -48)
        br = Vector( 48,  48)

        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        collision_detector.update_collidable(self.token, self.collidable)


    def update(self, t, dt, collision_detector):
        self.time_left -= dt

        all = collision_detector.collides(token=self.token,
                                          filters=self.filter)

        for c in all:
            try:
                c.shape2.owner.damage(t, dt * self.damage)
            except AttributeError:
                pass


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def alive(self):
        return self.time_left > 0.0


    def create_renderable(self):
        def wrapped(batch):
            return renderable.StaticSpriteRenderable(batch, self, 'fire_peak')
        return wrapped


FireboltAbility = Ability(Firebolt, 0.8)
