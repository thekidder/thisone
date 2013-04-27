import logging
import math

import pyglet.sprite

import imagecache
import kidgine.utils
import utils
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

Facing = kidgine.utils.enum('left', 'right', 'top', 'bottom')

class Character(object):
    idle_delay = 1.0
    idle_time  = 13 * 0.25

    """represents a character, player controlled or otherwise. has position and a facing"""
    def __init__(self):
        self.facing = Facing.left
        self.position = Vector(0, 0)
        self.moving = False
        self.time_to_idle = self.idle_delay
        self.idle = False


    def update(self, t, dt, direction):
        if direction.magnitude_sqr() > 0.1:
            self.time_to_idle = self.idle_delay
            self.moving = True
            self.idle = False
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
            self.time_to_idle -= dt
            self.moving = False

        if not self.idle and self.time_to_idle <= 0.0 and not self.moving:
            self.idle = True
            self.time_to_idle = 0

        if self.idle:
            self.time_to_idle += dt
            if self.time_to_idle >= self.idle_time:
                self.idle = False
                self.time_to_idle = 10.0

        self.position += dt * direction


class CharacterRenderable(object):
    def __init__(self, batch, character, sprite_base):
        self.character = character

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
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_left'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_right'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_top'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_bottom'),
                                                 batch = batch))

        #idle
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_idle'), batch = batch))



    def update(self):
        if self.character.idle:
            used_sprite_index = 8
        else:
            used_sprite_index = self.character.facing
            if self.character.moving:
                used_sprite_index += 4

        for i,sprite in enumerate(self.sprites):
            sprite.visible = (used_sprite_index == i)

        utils.set_sprite_pos(self.sprites[used_sprite_index], self.character.position)


    def delete(self):
        for i in self.sprites:
            self.sprites.delete()


class GirlCharacter(Character):
    def __init__(self):
        super(GirlCharacter, self).__init__()


    def get_sprite_name(self):
        return 'girl'
