import math

import ability
import collision
import data.animations
import kidgine.utils
import renderable
import kidgine.math.vector
from kidgine.math.vector import Vector
import random

Tags = kidgine.utils.enum('enemy', 'boss', 'player', 'dialog', 'projectile', 'ability', 'level', 'spike')

class TriggeredUpdatable(object):
    def __init__(self, trigger, action, persistent = False):
        self.trigger = trigger
        self.action = action
        self.triggered = False
        self.persistent = persistent


    def update(self, inputs, t, dt, collision_detector):
        if self.trigger(inputs, t, dt, collision_detector):
            self.triggered = True
            return self.action(inputs, t, dt, collision_detector)


    def removed(self, collision_detector):
        pass


    def create_renderable(self):
        return None


    def get_tags(self):
        return set()


    def alive(self):
        return not self.triggered and not self.persistent


class ActionEvent(TriggeredUpdatable):
    def __init__(self, action):
        def trigger(inputs, t, dt, collision_detector):
            return True
        super(ActionEvent, self).__init__(trigger, action)


class HUD(object):
    def __init__(self, scene):
        self.scene = scene
        self.active = [False] * 4
        self.cooldown = [False] * 4
        self.disabled = [False] * 4


    def removed(self, c):
        pass


    def update(self, inputs, t, dt, collision_detector):
        if not self.scene.player_character:
            self.disabled = [True] * 4
            for s in self.active:
                s = True
        else:
            if self.scene.player_character.ability_one:
                self.active[0]   = self.scene.player_character.ability_one.is_active(t)
                self.cooldown[0] = not self.scene.player_character.ability_one.is_recharged(t)
                self.disabled[0] = False
            else:
                self.disabled[0] = True
            if self.scene.player_character.ability_two:
                self.active[1]   = self.scene.player_character.ability_two.is_active(t)
                self.cooldown[1] = not self.scene.player_character.ability_two.is_recharged(t)
                self.disabled[1] = False
            else:
                self.disabled[1] = True
            if self.scene.player_character.ability_three:
                self.active[2]   = self.scene.player_character.ability_three.is_active(t)
                self.cooldown[2] = not self.scene.player_character.ability_three.is_recharged(t)
                self.disabled[2] = False
            else:
                self.disabled[2] = True
            if self.scene.player_character.ability_four:
                self.active[3]   = self.scene.player_character.ability_four.is_active(t)
                self.cooldown[3] = not self.scene.player_character.ability_four.is_recharged(t)
                self.disabled[3] = False
            else:
                self.disabled[3] = True


    def alive(self):
        return True


    def is_ui(self):
        return True


    def get_tags(self):
        return set()


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.HUDRenderable(batch, group, self)
        return wrapped


class Blinker(object):
    def __init__(self, parent, timer, color):
        self.last_blink = 0
        self.frame = 0
        self.parent = parent
        self.time_left = timer
        self.color = color
        self.parent.renderable.blinker.enable(False)


    def removed(self, c):
        self.parent.renderable.blinker.enable(True)


    def update(self, i, t, dt, c):
        self.time_left -= dt
        self.last_blink += dt

        blink_time = 0.4

        if self.last_blink > blink_time:
            self.last_blink = 0
            self.frame += 1
            if self.frame == 2:
                self.frame = 0

        if self.frame == 1:
            self.parent.renderable.sprites[self.parent.renderable.used_sprite_index].color = self.color
        else:
            self.parent.renderable.sprites[self.parent.renderable.used_sprite_index].color = (255, 255, 255)


    def alive(self):
        return self.time_left > 0.0


    def is_ui(self):
        return False


    def get_tags(self):
        return set()


    def create_renderable(self):
        return None



class Spike(object):
    counter = 0
    tags = set([Tags.spike])
    damage = 20
    added = False
    last_damage_time = 0
    cooldown = 0.4

    def __init__(self, position):
        self.position = position

        tl = Vector(-16, -16)
        br = Vector( 16,  16)

        self.token = 'spike{}'.format(Spike.counter)
        Spike.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([
                collision.Tags.ENVIRONMENT])


    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags or collision.Tags.ENEMY in shape.tags:
            if t - self.last_damage_time > self.cooldown:
                self.last_damage_time = t
                shape.owner.damage(t, self.damage)
                shape.owner.apply_force(-shape.owner.last.normalized() * 24)


    def slow(self, t, slow_factor, thing_that_is_slowing):
        pass


    def is_ui(self):
        return False


    def alive(self):
        return True


    def apply_force(self, force):
        pass


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def get_tags(self):
        return self.tags


    def update(self, inputs, t, dt, collision_detector):
        if not self.added:
            collision_detector.update_collidable(self.token, self.collidable)
            self.added = True


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.StaticSpriteRenderable(batch, group, self, 'spike', order = 1)
        return wrapped



class Bomb(object):
    explosion_time = data.animations.animation_duration('bomb_explosion')
    time = 1.5
    tags = set([Tags.projectile])
    counter = 0
    environment_filters = set([collision.Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
    damage = 10
    slow_time = 0
    slow_factor = 1.0

    def __init__(self, position, throw_vector):
        self.position = position
        self.forces = throw_vector
        self.time_left = self.time
        self.explosion_time_left = self.explosion_time
        self.explosion_triggered = False


        tl = Vector(-32, -32)
        br = Vector( 32,  32)

        self.token = 'bomb{}'.format(Bomb.counter)
        Bomb.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([
                collision.Tags.PROJECTILE,
                collision.Tags.PUSHABLE,
                collision.Tags.NOT_SLOWED])


    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags and not self.explosion_triggered:
            self._trigger()
            shape.owner.damage(t, self.damage)

        if collision.Tags.ENEMY in shape.tags and self.explosion_triggered:
            shape.owner.damage(t, self.damage)


    def slow(self, t, slow_factor, thing_that_is_slowing):
        if isinstance(thing_that_is_slowing, ability.Whirlpool):
            self.collidable.tags.discard(collision.Tags.NOT_SLOWED)
            self.slow_factor = slow_factor
            self.slow_time = t


    def is_ui(self):
        return False


    def alive(self):
        return self.explosion_time_left >= 0


    def apply_force(self, force):
        self.forces += force


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def get_tags(self):
        return self.tags


    def _trigger(self):
        self.explosion_triggered = True


    def update(self, inputs, t, dt, collision_detector):
        if not self.explosion_triggered:
            self.time_left -= dt

            if self.time_left <= 0.0:
                self._trigger()

            self.position = self.position + self.forces * self.slow_factor

            all = collision_detector.collides(token=self.token,
                                              filters=self.environment_filters)
            if len(all) > 0:
                normal = Vector()
                for c in all:
                    if normal.dot(c.translation_vector) == 0:
                        normal += c.translation_vector
                self.position += normal

            collision_detector.update_collidable(self.token, self.collidable)

        else:
            self.explosion_time_left -= dt

        self.reset_slow(t)


    def reset_slow(self, t):
        # if we haven't been slowed in a while, reset
        if t - self.slow_time > 0.4:
            self.collidable.tags.add(collision.Tags.NOT_SLOWED)
            self.slow_factor = 1.0


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.BombRenderable(batch, group, self)
        return wrapped



class Spear(Bomb):
    time = 1.0
    time_left = 0
    tags = set([Tags.projectile])
    counter = 0
    environment_filters = set([collision.Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
    damage = 10

    def __init__(self, position, throw_vector):
        self.position = position
        self.forces = throw_vector
        self.forced = False
        self.time_left = self.time

        tl = Vector(-20, -20)
        br = Vector( 20,  20)

        self.token = 'spear{}'.format(Spear.counter)
        Spear.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([
                collision.Tags.PUSHABLE])

    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags or \
                collision.Tags.ENEMY in shape.tags and self.forced:
            shape.owner.damage(t, self.damage)
            self.time_left = 0

    def alive(self):
        return self.time_left >= 0

    def apply_force(self, force):
        self.forces += force
        self.forced = True
        self.time_left = 1.0

    def update(self, inputs, t, dt, collision_detector):
        self.time_left -= dt

        self.position = self.position + self.forces

        all = collision_detector.collides(token=self.token,
                                          filters=self.environment_filters)
        if len(all) > 0:
            normal = Vector()
            for c in all:
                if normal.dot(c.translation_vector) == 0:
                    normal += c.translation_vector
            self.position += normal

        collision_detector.update_collidable(self.token, self.collidable)

    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.SpearRenderable(batch, group, self)
        return wrapped



class OpacityFader(object):
    def __init__(self, color, start, end, duration):
        self.r,self.g,self.b = color
        self.start = start
        self.end = end
        self.duration = duration
        self.time_left = duration
        self.opacity = start


    def removed(self, c):
        pass


    def update(self, inputs, t, dt, collision_detector):
        self.time_left -= dt
        self.opacity = kidgine.utils.lerp(
            (self.duration - self.time_left) / self.duration,
            self.start,
            self.end)


    def alive(self):
        return self.time_left >= 0


    def is_ui(self):
        return True


    def get_tags(self):
        return set()


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.OpacityFaderRenderable(batch, group, self)
        return wrapped


def fade_to_black(duration):
    return OpacityFader((0,0,0),0,1,duration)


def fade_from_black(duration):
    return OpacityFader((0,0,0),1,0,duration)
