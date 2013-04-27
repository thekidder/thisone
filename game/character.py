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
    """represents a character, player controlled or otherwise. has position and a facing"""
    def __init__(self):
        self.facing = Facing.left
        self.position = Vector(0, 0)
        self.moving = False


    def move(self, velocity):
        if velocity.magnitude_sqr() > 0.1:
            self.moving = True
            if math.fabs(velocity.x) > math.fabs(velocity.y):
                if velocity.x > 0:
                    self.facing = Facing.right
                else:
                    self.facing = Facing.left
            else:
                if velocity.y > 0:
                    self.facing = Facing.top
                else:
                    self.facing = Facing.bottom
        else:
            self.moving = False

        self.position += velocity


class CharacterRenderable(object):
    def __init__(self, batch, character, sprite_base):
        self.character = character

        self.sprites = list()
        # 0-3: left,right,top,bottom
        # 4-7: walk; left,right,top,bottom
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_left'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_right'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_top'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_bottom'), batch = batch))

        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_left'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_right'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_top'),
                                                 batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_animation(sprite_base + '_walk_bottom'),
                                                 batch = batch))



    def update(self):
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
