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


    def move(self, velocity):
        if velocity.magnitude_sqr() > 0.1:
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

        self.position += velocity


class CharacterRenderable(object):
    def __init__(self, batch, character, sprite_base):
        self.character = character

        self.sprites = list()
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_left'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_right'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_top'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_bottom'), batch = batch))


    def update(self):
        for i in xrange(4):
            self.sprites[i].visible = (self.character.facing == i)

        utils.set_sprite_pos(self.sprites[self.character.facing], self.character.position)


    def delete(self):
        for i in self.sprites:
            self.sprites.delete()


class TestCharacter(Character):
    def __init__(self):
        super(TestCharacter, self).__init__()


    def get_sprite_name(self):
        return 'test'
