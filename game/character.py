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
        self.idle_time = data.animations.animation_duration(self.get_sprite_name() + '_idle')


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
        self.position += dt * direction



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



    def update(self):
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


class CollidableCharacter(Character):
    counter = 0
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

        # resolve collision
        collision = collision_detector.can_move_to(self.token, self.position)
        if collision is not None:
            self.position += collision.translation_vector
        collision_detector.update_collidable(self.token, self.collidable)



class GirlCharacter(CollidableCharacter):
    def __init__(self, inputs, collision_detector):
        super(GirlCharacter, self).__init__(collision_detector)

        self.inputs = inputs


    def update(self, t, dt, collision_detector):
        # move to new position
        direction = Vector(self.inputs.leftright * 100, self.inputs.updown * 100)
        super(GirlCharacter, self).update(t, dt, direction, collision_detector)


    def get_sprite_name(self):
        return 'girl'


class MeleeEnemy(CollidableCharacter):
    def __init__(self, target, collision_detector):
        super(MeleeEnemy, self).__init__(collision_detector)
        self.target = target


    def update(self, t, dt, collision_detector):
        direction = (self.target.position - self.position).normalized()
        direction *= 90

        super(MeleeEnemy, self).update(t, dt, direction, collision_detector)


    def get_sprite_name(self):
        return 'test'
