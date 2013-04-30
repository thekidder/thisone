import logging
import math

import ability
import data.animations
import kidgine.collision.rectangle
import kidgine.collision.shape
import kidgine.math.vector
import kidgine.utils
import renderable
import collision
import updatable
from kidgine.math.vector import Vector
import random


logger = logging.getLogger(__name__)
health_scaling = 1.0

Facing = kidgine.utils.enum('left', 'right', 'top', 'bottom')
MoveDirection = kidgine.utils.enum(
    'right',
    'righttop',
    'top',
    'lefttop',
    'left',
    'leftbottom',
    'bottom',
    'rightbottom')

class Character(object):
    tags = set()
    idle_delay     = 3.0
    idle_delay_two = 4.0
    last = Vector()

    """represents a character, player controlled or otherwise. has position and a facing"""
    def __init__(self, position):
        self.facing = Facing.left
        self.position = position
        self.moving = False
        self.time_to_idle = self.idle_delay
        self.idle = False
        self.idle_time = data.animations.animation_duration(self.renderable_type.sprite_name + '_idle')
        if isinstance(self, GirlCharacter):
            self.health = self.max_health
        else:
            self.health = self.max_health * health_scaling
        self.last_hit = 0

    def update(self, t, dt, direction):
        if direction.magnitude_sqr() > 0.1:
            self.last = direction
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



    def damage(self, t, amount):
        self.last_hit = t
        self.health = max(0, self.health - amount)


    def alive(self):
        return self.health > 0.0


    def collides(self, t, shape):
        pass


    def get_tags(self):
        return self.tags


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


    def is_ui(self):
        return False


    def create_renderable(self):
        def wrapped(batch, group):
            return self.renderable_type(batch, group, self)
        return wrapped



class CollidableCharacter(Character):
    counter = 0
    environment_filters = set([collision.Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])

    def __init__(self, position):
        super(CollidableCharacter, self).__init__(position)

        tl = Vector(-16, 0)
        br = Vector( 16, 32)

        self.token = 'character{}'.format(CollidableCharacter.counter)
        CollidableCharacter.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])

        self.forces = Vector()


    def apply_force(self, force, debug=False):
        if debug:
            print self
            print 'incoming force', force
            print 'old forces', self.forces
        self.forces += force
        if debug:
            print 'new forces', self.forces


    def reset_force(self):
        self.forces = Vector()


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def update(self, inputs, t, dt, direction, collision_detector):
        super(CollidableCharacter, self).update(t, dt, direction)
        self.position = self.position + direction * dt + self.forces

        all = collision_detector.collides(token=self.token,
                                          filters=self.environment_filters)
        if len(all) > 0:
            normal = Vector()
            for c in all:
                if normal.dot(c.translation_vector) == 0:
                    normal += c.translation_vector
            self.position += normal

        collision_detector.update_collidable(self.token, self.collidable)

        self.reset_force()


class GirlCharacter(CollidableCharacter):
    tags = set([updatable.Tags.player])
    max_health = 80.0
    regen_delay = 2
    regen_rate = 30 # units/sec
    renderable_type = renderable.GirlRenderable

    def __init__(self, position):
        super(GirlCharacter, self).__init__(position)

        self.move_direction = MoveDirection.left

        self.collidable.tags = set([
                kidgine.collision.shape.tags.IMPEEDS_MOVEMENT,
                collision.Tags.PLAYER,
                collision.Tags.MOVEABLE])

        self.ability_one   = ability.Ability(ability.Firebolt,   0.8)
        self.ability_two   = ability.Ability(ability.Whirlpool,  4.5)
        self.ability_three = ability.Ability(ability.Windblast,  2.5)
        self.ability_four  = ability.Ability(ability.Earthquake, 1.6)


    def update(self, inputs, t, dt, collision_detector):
        # move to new position
        direction = Vector(inputs.leftright, inputs.updown)
        self._set_move_dir(inputs.leftright, inputs.updown)
        direction = direction.normalized() * 140.0
        super(GirlCharacter, self).update(inputs, t, dt, direction, collision_detector)

        # activate abilities
        new_objs = list()
        if self.ability_one and inputs.one:
            self.ability_one.activate(t, dt, collision_detector, self, new_objs)
        if self.ability_two and inputs.two:
            self.ability_two.activate(t, dt, collision_detector, self, new_objs)
        if self.ability_three and inputs.three:
            self.ability_three.activate(t, dt, collision_detector, self, new_objs)
        if self.ability_four and inputs.four:
            self.ability_four.activate(t, dt, collision_detector, self, new_objs)

        # regen health
        if t - self.last_hit > self.regen_delay:
            self.health += self.regen_rate * dt
            self.health = min(self.max_health, self.health)

        return new_objs

    def _set_move_dir(self, leftright, updown):
        if   leftright == -1 and updown ==  1:
            self.move_direction = MoveDirection.leftbottom
        elif leftright == -1 and updown ==  0:
            self.move_direction = MoveDirection.left
        elif leftright == -1 and updown == -1:
            self.move_direction = MoveDirection.lefttop
        elif leftright ==  0 and updown ==  1:
            self.move_direction = MoveDirection.bottom
        elif leftright ==  0 and updown == -1:
            self.move_direction = MoveDirection.top
        elif leftright ==  1 and updown ==  1:
            self.move_direction = MoveDirection.rightbottom
        elif leftright ==  1 and updown ==  0:
            self.move_direction = MoveDirection.right
        elif leftright ==  1 and updown == -1:
            self.move_direction = MoveDirection.righttop


class MeleeEnemy(CollidableCharacter):
    tags = set([updatable.Tags.enemy])
    player_filter = set([collision.Tags.PLAYER])
    damage_delay = 0.5
    max_health = 60.0
    base_damage = 10
    base_force = 16
    speed = 90
    renderable_type = renderable.MeleeEnemyRenderable

    def __init__(self, position, target):
        super(MeleeEnemy, self).__init__(position)
        self.target = target
        self.collidable.tags = set([
                kidgine.collision.shape.tags.IMPEEDS_MOVEMENT,
                collision.Tags.MOVEABLE,
                collision.Tags.ENEMY,
                collision.Tags.PUSHABLE,
                collision.Tags.NOT_SLOWED])
        self.last_damage_time = 0
        self.slow_factor = 1.0
        self.slow_time = 0


    def slow(self, t, slow_factor, thing_that_is_slowing):
        self.collidable.tags.discard(collision.Tags.NOT_SLOWED)
        self.slow_factor = slow_factor
        self.slow_time = t


    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags:
            self.do_damage(t, shape)


    def do_damage(self, t, shape):
        if t - self.last_damage_time > self.damage_delay:
            self.last_damage_time = t
            try:
                shape.owner.damage(t, self.base_damage)
                shape.owner.apply_force((shape.owner.position - self.position).normalized() * self.base_force)
            except AttributeError:
                pass


    def reset_slow(self, t):
        # if we haven't been slowed in a while, reset
        if t - self.slow_time > 0.4:
            self.collidable.tags.add(collision.Tags.NOT_SLOWED)
            self.slow_factor = 1.0


    def update(self, inputs, t, dt, collision_detector):
        direction = kidgine.math.vector.constant_zero
        if self.target:
            direction = (self.target.position - self.position).normalized()
            direction *= self.speed * self.slow_factor

        super(MeleeEnemy, self).update(inputs, t, dt, direction, collision_detector)

        self.reset_slow(t)


class BombEnemy(MeleeEnemy):
    speed = 70
    bomb_speed = 150 * (1/60.)
    throw_delay = 3.5


    def __init__(self, position, target):
        super(BombEnemy, self).__init__(position, target)
        self.last_damage_time = random.uniform(0.0, self.throw_delay)


    def collides(self, t, shape):
        # no melee attack
        pass


    def update(self, inputs, t, dt, collision_detector):
        bomb = None

        direction = Vector(0.0,0.0)
        if self.target:
            target_vector = self.target.position - self.position
            if target_vector.shorter_than(128):
                # move away from target
                direction = -target_vector.normalized()
            elif target_vector.shorter_than(256) and t - self.last_damage_time > self.throw_delay:
                self.last_damage_time = t
                # throw bomb
                bomb = updatable.Bomb(self.position, target_vector.normalized() * self.bomb_speed)
            elif target_vector.shorter_than(512):
                # move toward target
                direction = target_vector.normalized()

            direction *= self.speed * self.slow_factor

        super(MeleeEnemy, self).update(inputs, t, dt, direction, collision_detector)

        self.reset_slow(t)

        if bomb:
            return [bomb]
        else:
            return []


class SpearEnemy(MeleeEnemy):
    speed = 70
    spear_speed = 250 * (1/60.)
    throw_delay = 3


    def __init__(self, position, target):
        super(SpearEnemy, self).__init__(position, target)
        self.last_damage_time = random.uniform(0.0, self.throw_delay)


    def update(self, inputs, t, dt, collision_detector):
        spear = None

        direction = Vector(0.0,0.0)
        if self.target:
            target_vector = self.target.position - self.position
            if target_vector.shorter_than(128):
                # move away from target
                direction = -target_vector.normalized()
            elif target_vector.shorter_than(256) and t - self.last_damage_time > self.throw_delay:
                self.last_damage_time = t
                # throw spear
                spear = updatable.Spear(self.position, target_vector.normalized() * self.spear_speed)
            elif target_vector.shorter_than(512):
                # move toward target
                direction = target_vector.normalized()

            direction *= self.speed * self.slow_factor

        super(MeleeEnemy, self).update(inputs, t, dt, direction, collision_detector)

        self.reset_slow(t)

        if spear:
            return [spear]
        else:
            return []


class WarlordBoss(MeleeEnemy):
    tags = set([updatable.Tags.enemy, updatable.Tags.boss])
    max_health = 300.0
    base_damage = 35
    base_force = 30.0
    normal_speed = 45
    charge_speed = 450
    speed = 45
    renderable_type = renderable.WarlordRenderable
    charging = None
    charge_delay = 0.45
    charge_length = 1
    charge_rest = 1.25
    charge_direction = None
    first_spawn_delay = 2.0

    def slow(self, t, slow_factor, thing_that_is_slowing):
        super(WarlordBoss, self).slow(t, slow_factor, thing_that_is_slowing)
        # Reduce slows by 90%
        self.slow_factor = (1.0 - (1.0 - self.slow_factor) * 0.1)

    def apply_force(self, force, debug=False):
        # Reduce forces by 90%
        force *= 0.1
        super(WarlordBoss, self).apply_force(force, debug)

    def update(self, inputs, t, dt, collision_detector):
        self.first_spawn_delay = max(self.first_spawn_delay - dt, 0)

        direction = Vector(0.0,0.0)
        if self.target:
            # Adjusting position, preparing to charge.
            target_vector = self.target.position - self.position
            direction = self.target.position - self.position
            if abs(direction.x) > abs(direction.y):
                direction.x = 0
            else:
                direction.y = 0
            if self.charging or (direction.magnitude() < 30.0 and self.first_spawn_delay == 0.0):
                # Currently charging OR beginning a charge.
                direction *= 0
                if not self.charging:
                    self.charging = t
                elif t - (self.charge_delay + self.charge_length + self.charge_rest) > self.charging:
                    # Done resting.
                    self.charging = None
                    self.charge_direction = None
                    self.speed = self.normal_speed
                elif t - (self.charge_delay + self.charge_length) > self.charging:
                    # Resting from a charge.
                    pass
                elif t - self.charge_delay > self.charging:
                    # Waited a full second, charging now.
                    if not self.charge_direction:
                        if abs(target_vector.x) > abs(target_vector.y):
                            direction.x = math.copysign(1, target_vector.x)
                        else:
                            direction.y = math.copysign(1, target_vector.y)
                        self.charge_direction = direction.normalized()
                    else:
                        direction = self.charge_direction.normalized()
                    self.speed = self.charge_speed
                else:
                    direction = kidgine.math.vector.constant_zero

            direction = direction.normalized()
            direction *= self.speed * self.slow_factor

        collision_info = collision_detector.collides(token=self.token, filters=self.player_filter)
        if collision_info is not None:
            self.do_damage(t, collision_info)

        super(MeleeEnemy, self).update(inputs, t, dt, direction, collision_detector)

        self.reset_slow(t)


class ChieftainBoss(WarlordBoss):
    tags = set([updatable.Tags.enemy, updatable.Tags.boss])
    max_health = 100.0
    base_damage = 25
    base_force = 30.0
    normal_speed = 45
    charge_speed = 450
    speed = 45
    renderable_type = renderable.ChieftainRenderable
    charging = None
    charge_delay = 0.45
    charge_length = 1
    charge_rest = 1.25
    charge_direction = None
    first_spawn_delay = 2.0
