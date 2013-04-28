import logging
import math

import kidgine.collision.circle
import kidgine.collision.rectangle
import renderable
from collision import Tags
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

class Ability(object):
    def __init__(self, ability_type, recharge_time):
        self.ability_type = ability_type
        self.recharge_time = recharge_time
        self.last_activation = -60


    def activate(self, t, dt, collision_detector, parent, new_objs):
        if t - self.last_activation > self.recharge_time:
            self.last_activation = t

            new_objs.append(self.ability_type(parent, collision_detector))


# stays around for a certain duration applying an effect to all collidables
class TimedAbility(object):
    filter = set([Tags.ENEMY])
    pulse = False

    def __init__(self):
        self.time_left = self.duration
        self.rotation = 0.0
        self.last_trigger_time = -60


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def update(self, t, dt, collision_detector):
        self.time_left -= dt

        if not self.pulse or t - self.last_trigger_time > self.pulse_rate:
            self.last_trigger_time = t
            all = collision_detector.collides(token=self.token,
                                              filters=self.filter)

            for c in all:
                self.apply(t, dt, c)


    def alive(self):
        return self.time_left > 0.0


    def create_renderable(self):
        def wrapped(batch):
            return renderable.StaticSpriteRenderable(batch, self, self.sprite_name, rotation=self.rotation)
        return wrapped


class Firebolt(TimedAbility):
    damage = 80 # per second
    duration = 0.2
    sprite_name = 'fire_peak'

    def __init__(self, parent, collision_detector):
        super(Firebolt, self).__init__()
        self.rotation = parent.move_direction * 45.0

        offset = kidgine.math.vector.from_radians(math.radians(self.rotation)) * 48
        offset.y = -offset.y
        self.position = (parent.position
                         + offset
                         + Vector(0, 16))

        self.token = 'firebolt'

        tl = Vector(-48, -48)
        br = Vector( 48,  48)

        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.rotation = self.rotation
        collision_detector.update_collidable(self.token, self.collidable)


    def update(self, t, dt, collision_detector):
        super(Firebolt, self).update(t, dt, collision_detector)


    def apply(self, t, dt, c):
        try:
            c.shape2.owner.damage(t, dt * self.damage)
        except AttributeError:
            pass


class Earthquake(TimedAbility):
    filter = set([Tags.ENEMY, Tags.NOT_SLOWED])
    duration = 1.4
    slow = 0.5
    sprite_name = 'earth_peak'
    size = 48
    pulse = True
    pulse_rate = 0.4

    def __init__(self, parent, collision_detector):
        super(Earthquake, self).__init__()

        self.position = parent.position + Vector(0, 16)

        tl = Vector(-self.size, -self.size)
        br = Vector( self.size,  self.size)
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)

        self.token = 'earthquake'
        #self.collidable = kidgine.collision.circle.Circle(self, self.position, self.size)

        collision_detector.update_collidable(self.token, self.collidable)


    def apply(self, t, dt, c):
        self.last_trigger = t
        try:
            c.shape2.owner.slow(t, self.slow)
        except AttributeError:
            pass


    def update(self, t, dt, collision_detector):
        super(Earthquake, self).update(t, dt, collision_detector)





FireboltAbility   = Ability(Firebolt, 0.8)
EarthquakeAbility = Ability(Earthquake, 1.6)
