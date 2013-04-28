import logging
import math

import data.animations
import kidgine.collision.rectangle
import kidgine.collision.shape
import kidgine.math.vector
import kidgine.utils
import renderables
from collision import Tags
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

Facing = kidgine.utils.enum('left', 'right', 'top', 'bottom')

class Character(object):
    idle_delay     = 3.0
    idle_delay_two = 4.0

    """represents a character, player controlled or otherwise. has position and a facing"""
    def __init__(self):
        self.facing = Facing.left
        self.position = Vector(0, 0)
        self.moving = False
        self.time_to_idle = self.idle_delay
        self.idle = False
        self.idle_time = data.animations.animation_duration(self.renderable_type.sprite_name + '_idle')


    def update(self, t, dt, direction):
        if direction.magnitude_sqr() > 0.1:
            self.moving = True
            if math.fabs(direction.x) > math.fabs(direction.y):
                if direction.x > 0:
                    self.facing = Facing.right
                else:
                    self.facing = Facing.left
            else:
                if direction.y > 0:
                    self.facing = Facing.top
                else:
                    self.facing = Facing.bottom
        else:
            self.moving = False

        self.update_idle(t, dt)


    def collides(self, t, shape):
        pass


    def update_idle(self, t, dt):
        if self.moving:
            self.time_to_idle = self.idle_delay
            self.idle = False
        else:
            self.time_to_idle -= dt

            if self.time_to_idle <= 0.0:
                if self.idle:
                    self.idle = False
                    self.time_to_idle = self.idle_delay_two
                else:
                    self.idle = True
                    self.time_to_idle = self.idle_time


    def create_renderable(self):
        def wrapped(batch):
            return self.renderable_type(batch, self)
        return wrapped



class CollidableCharacter(Character):
    counter = 0
    environment_filters = set([Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])

    def __init__(self, collision_detector):
        super(CollidableCharacter, self).__init__()

        tl = Vector(-16,   0)
        br = Vector( 16,  32)

        self.token = 'character{}'.format(CollidableCharacter.counter)
        CollidableCharacter.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])

        collision_detector.update_collidable(self.token, self.collidable)

        self.forces = Vector()


    def apply_force(self, force):
        self.forces += force


    def reset_force(self):
        self.forces = Vector()


    def update(self, t, dt, direction, collision_detector):
        super(CollidableCharacter, self).update(t, dt, direction)
        candidate_pos = self.position + direction * dt + self.forces

        all = collision_detector.collides(token=self.token, position = candidate_pos,
                                          filters=self.environment_filters)
        if len(all) == 0:
            self.position = candidate_pos
        else:
            normal = Vector()
            for c in all:
                if normal.dot(c.translation_vector) == 0:
                    normal += c.translation_vector
            self.position = candidate_pos + normal

        collision_detector.update_collidable(self.token, self.collidable)


class GirlCharacter(CollidableCharacter):
    max_health = 80.0
    regen_delay = 2
    regen_rate = 30 # units/sec
    renderable_type = renderables.GirlRenderable

    def __init__(self, inputs, collision_detector):
        super(GirlCharacter, self).__init__(collision_detector)

        self.inputs = inputs
        self.health = 80.0
        self.last_hit = 0

        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT, Tags.PLAYER, Tags.MOVEABLE])


    def update(self, t, dt, collision_detector):
        # move to new position
        direction = Vector(self.inputs.leftright, self.inputs.updown)
        direction = direction.normalized() * 140.0
        super(GirlCharacter, self).update(t, dt, direction, collision_detector)

        if t - self.last_hit > self.regen_delay:
            self.health += self.regen_rate * dt
            self.health = min(self.max_health, self.health)


    def damage(self, t, amount):
        self.last_hit = t
        self.health = max(0, self.health - amount)


class MeleeEnemy(CollidableCharacter):
    player_filter = set([Tags.PLAYER])
    damage_delay = 0.5
    max_health = 80.0
    renderable_type = renderables.MeleeEnemyRenderable

    def __init__(self, target, collision_detector):
        super(MeleeEnemy, self).__init__(collision_detector)
        self.target = target
        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT, Tags.MOVEABLE, Tags.ENEMY])
        self.last_damage_time = 0
        self.health = self.max_health


    def collides(self, t, shape):
        self.do_damage(t, shape)


    def do_damage(self, t, shape):
        if t - self.last_damage_time > self.damage_delay:
            self.last_damage_time = t
            try:
                shape.owner.damage(t, 10)
                shape.owner.apply_force((shape.owner.position - self.position).normalized() * 16)
            except AttributeError:
                pass


    def update(self, t, dt, collision_detector):
        direction = kidgine.math.vector.constant_zero
        if self.target:
            direction = (self.target.position - self.position).normalized()
            direction *= 90

        collision = collision_detector.collides(token=self.token, filters=self.player_filter)
        if collision is not None:
            self.do_damage(t, collision)

        super(MeleeEnemy, self).update(t, dt, direction, collision_detector)
