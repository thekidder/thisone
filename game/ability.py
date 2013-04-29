import logging
import math

import kidgine.collision.circle
import kidgine.collision.rectangle
import renderable
import random
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
    order = 5

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
        def wrapped(batch, group):
            return renderable.StaticSpriteRenderable(batch, group, self,
                                                     self.sprite_name, rotation=self.rotation, order=self.order)
        return wrapped


class Firebolt(TimedAbility):
    damage = 80 # per second
    duration = 0.2
    sprite_name = 'fire_peak'
    order = 15

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
        self.last_trigger_time = t
        try:
            c.shape2.owner.slow(t, self.slow)
        except AttributeError:
            pass


    def update(self, t, dt, collision_detector):
        super(Earthquake, self).update(t, dt, collision_detector)


class Windblast(TimedAbility):
    filter = set([Tags.ENEMY])
    duration = 0.7
    force = 500

    spread = 0.8 #radians
    sprite_name = 'wind_peak'
    size = 48
    slow = 0.1
    duration = 1.0

    order = 15

    def __init__(self, parent, collision_detector):
        super(Windblast, self).__init__()

        self.parent = parent
        self.position = parent.position + Vector(0, 16)

        tl = Vector(-self.size, -self.size)
        br = Vector( self.size,  self.size)
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)

        self.token = 'windblast'

        collision_detector.update_collidable(self.token, self.collidable)

    def apply(self, t, dt, c):
        p1 = c.shape1.owner.position
        p2 = c.shape2.owner.position
        start_vector = Vector(p2.x - p1.x, p2.y - p1.y)
        eject_mag = self.force  / (start_vector.magnitude() / self.size )
        eject_vector = start_vector.normalized().rotate((random.random() - 0.5) * self.spread)
        eject_vector *= (eject_mag * dt)
        c.shape2.owner.apply_force(eject_vector)
        c.shape2.owner.slow(t, self.slow)

    def update(self, t, dt, collision_detector):
        self.position = self.parent.position + Vector(0, 16)
        collision_detector.update_collidable(self.token, self.collidable)
        super(Windblast, self).update(t, dt, collision_detector)


class Whirlpool(TimedAbility):
    filter = set([Tags.ENEMY])
    duration = 4
    sprite_name = 'water_peak'
    size = 48
    distance = 132
    force_mult = 2.5
    pulse = True
    pulse_rate = 0.4
    min_slow = 0.9
    slow_scale = 0.08

    def __init__(self, parent, collision_detector):
        super(Whirlpool, self).__init__()

        self.rotation = parent.move_direction * 45

        offset = kidgine.math.vector.from_radians(math.radians(self.rotation)) * 132
        offset.y = -offset.y
        self.position = (parent.position
                         + offset)

        tl = Vector(-self.size, -self.size)
        br = Vector( self.size,  self.size)
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)

        self.token = 'whirlpool'

        collision_detector.update_collidable(self.token, self.collidable)


    def apply(self, t, dt, c):
        self.last_trigger_time = t
        try:
            # Pull is at a 45 degree slant, getting straighter and weaker toward the middle.
            # Slow is weak, getting stronger toward the middle.
            p1 = c.shape1.owner.position
            p2 = c.shape2.owner.position
            start_vector = Vector(p1.x - p2.x, p1.y - p2.y)
            svmag = start_vector.magnitude()
            pull_mag = svmag * self.force_mult * self.pulse_rate
            pull_vector = start_vector.normalized().rotate(math.radians(-(45*(1-(self.size / (self.size + svmag))))))
            pull_vector *= pull_mag**0.5
            c.shape2.owner.apply_force(pull_vector)
            c.shape2.owner.slow(t, min(self.min_slow, self.min_slow / (pull_mag * self.slow_scale)))
        except AttributeError:
            pass


    def update(self, t, dt, collision_detector):
        super(Whirlpool, self).update(t, dt, collision_detector)


FireboltAbility   = Ability(Firebolt, 0.8)
EarthquakeAbility = Ability(Earthquake, 1.6)
WindblastAbility = Ability(Windblast, 2.5)
WhirlpoolAbility = Ability(Whirlpool, 4.5)
