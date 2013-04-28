import logging
import math

import pyglet.sprite

import data.animations
import imagecache
import kidgine.collision.rectangle
import kidgine.collision.shape
import kidgine.utils
import sprite
import utils
from kidgine.math.vector import Vector
from collision import Tags


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
        self.idle_time = data.animations.animation_duration(self.renderable_type().sprite_name + '_idle')


    def update(self, t, dt, direction):
        if direction.magnitude_sqr() > 0.1:
            self.position += dt * direction
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


    def update(self, t, dt, direction, collision_detector):
        super(CollidableCharacter, self).update(t, dt, direction)

        if self.moving:
            # resolve collision
            collision = collision_detector.can_move_to(self.token, self.position)
            if collision is not None:
                if Tags.MOVEABLE in collision.shape2.tags:
                    self.position += 0.20 * collision.translation_vector
                    if collision_detector.collides(token=collision.token2, filters=self.environment_filters) is None:
                        collision.shape2.owner.position -= 0.25 * collision.translation_vector
                else:
                    self.position += collision.translation_vector
            collision_detector.update_collidable(self.token, self.collidable)


class GirlCharacter(CollidableCharacter):
    max_health = 80.0
    regen_delay = 2
    regen_rate = 30 # units/sec
    def __init__(self, inputs, collision_detector):
        super(GirlCharacter, self).__init__(collision_detector)

        self.inputs = inputs
        self.health = 10.0
        self.last_hit = 0

        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
        self.collidable.tags.add(Tags.PLAYER)


    def update(self, t, dt, collision_detector):
        # move to new position
        direction = Vector(self.inputs.leftright * 100, self.inputs.updown * 100)
        super(GirlCharacter, self).update(t, dt, direction, collision_detector)

        if t - self.last_hit > self.regen_delay:
            self.health += self.regen_rate * dt
            self.health = min(self.max_health, self.health)


    def damage(self, t, amount):
        self.last_hit = t
        self.health = max(0, self.health - amount)


    def renderable_type(self):
        return GirlRenderable


class MeleeEnemy(CollidableCharacter):
    player_filter = set([Tags.PLAYER])

    def __init__(self, target, collision_detector):
        super(MeleeEnemy, self).__init__(collision_detector)
        self.target = target
        self.collidable.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
        self.collidable.tags.add(Tags.MOVEABLE)


    def do_damage(self, t, collision):
        try:
            collision.shape2.owner.damage(t, 10)
        except AttributeError:
            pass


    def update(self, t, dt, collision_detector):
        direction = (self.target.position - self.position).normalized()
        direction *= 90

        collision = collision_detector.collides(token=self.token, filters=self.player_filter)
        if collision is not None:
            self.do_damage(t, collision)

        super(MeleeEnemy, self).update(t, dt, direction, collision_detector)


    def renderable_type(self):
        return MeleeEnemyRenderable


class CharacterRenderable(object):
    def __init__(self, batch, character, sprite_base):
        self.character = character
        self.last_sprite_index = 0

        self.sprites = list()
        # 0-3 : left,right,top,bottom
        # 4-7 : walk; left,right,top,bottom
        # 8   : idle

        # stationary
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_left'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_right'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_top'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_bottom'), batch = batch))

        # walk
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_left'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_right'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_top'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_bottom'),
                                                  batch = batch))

        #idle
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_idle'), batch = batch))


    def update(self, t, dt):
        if self.character.idle:
            used_sprite_index = 8
        else:
            used_sprite_index = self.character.facing
            if self.character.moving:
                used_sprite_index += 4

        if used_sprite_index != self.last_sprite_index:
            new = self.sprites[used_sprite_index]
            if isinstance(new, sprite.AnimatedSprite):
                new.set_frame(0)
                new.play()

            self.last_sprite_index = used_sprite_index

        for i,s in enumerate(self.sprites):
            s.visible = (used_sprite_index == i)

        utils.set_sprite_pos(self.sprites[used_sprite_index], self.character.position)


    def delete(self):
        for i in self.sprites:
            self.sprites.delete()


class MeleeEnemyRenderable(CharacterRenderable):
    sprite_name = 'test'
    def __init__(self, batch, character):
        super(MeleeEnemyRenderable, self).__init__(batch, character, self.sprite_name)


class GirlRenderable(CharacterRenderable):
    sprite_name = 'girl'
    def __init__(self, batch, character):
        super(GirlRenderable, self).__init__(batch, character, self.sprite_name)
        self.last_blink = 0
        self.frame = 0


    def update(self, t, dt):
        super(GirlRenderable, self).update(t, dt)

        if self.character.max_health - self.character.health < 10.1:
            self.frame = 0
        else:
            self.last_blink += dt

            blink_time = 0.4 * (1.0 - (self.character.max_health - self.character.health) / 80.0)

            if self.last_blink > blink_time:
                self.last_blink = 0
                self.frame += 1
                if self.frame == 2:
                    self.frame = 0

        if self.frame == 1:
            self.sprites[self.last_sprite_index].color = (255, 128, 128)
        else:
            self.sprites[self.last_sprite_index].color = (255, 255, 255)
