import logging
import math

import pyglet.sprite

import data.animations
import imagecache
import kidgine.utils
import sprite
import utils
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

Facing = kidgine.utils.enum('left', 'right', 'top', 'bottom')

class Character(object):
    idle_delay     = 1.0
    idle_delay_two = 5.0

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


class GirlCharacter(Character):
    def __init__(self):
        super(GirlCharacter, self).__init__()


    def get_sprite_name(self):
        return 'girl'
