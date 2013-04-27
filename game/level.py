import json
import logging
import os.path

import pyglet.graphics
import pyglet.sprite

import kidgine.collision.rectangle
import kidgine.collision.shape
import tileset
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

def load(filename, collision_detector=None):
    with open(filename) as f:
        json_level = json.load(f)

    l = None
    if collision_detector is not None:
        l = Level(filename, json_level, collision_detector)
    r= LevelRenderable(filename, json_level)

    return l,r


class Level(object):
    def __init__(self, filename, json_level, collision_detector):
        tiles = _get_tileset(filename, json_level['tilesets'][0]['image'])

        width  = json_level['layers'][0]['width']
        height = json_level['layers'][0]['height']

        for layer in json_level['layers']:
            for i,tile in enumerate(layer['data']):
                if tile == 0:
                    continue

                if not tiles.collides(tile):
                    continue

                x = 32 * (i % width)
                y = 32 * (height - i / width)

                center = Vector(x + 16, y + 16)
                tl = Vector(-16, -16)
                br = Vector(16, 16)

                token = '{}_{}_{}'.format(filename, x, y)
                c = kidgine.collision.rectangle.Rectangle(None, tl, br, center = center)
                c.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
                collision_detector.update_collidable(token, c)


class LevelRenderable(object):
    tile_width = 32
    tile_height = 32

    def __init__(self, filename, json_level):
        tiles = _get_tileset(filename, json_level['tilesets'][0]['image'])
        self.batch = pyglet.graphics.Batch()
        self.sprites = list()

        width  = json_level['layers'][0]['width']
        height = json_level['layers'][0]['height']
        for layer in json_level['layers']:
            for i,tile in enumerate(layer['data']):
                if tile == 0:
                    continue

                x = i % width
                y = height - i / width

                s = pyglet.sprite.Sprite(tiles.get(tile), batch=self.batch)
                s.x = x * self.tile_width
                s.y = y * self.tile_height
                self.sprites.append(s)


    def draw(self):
        self.batch.draw()


def _get_tileset(filename, path):
        tileset_path = os.path.join(os.path.dirname(filename), path)
        tileset_path = os.path.normcase(os.path.normpath(tileset_path))
        # this is hacky: pyglet.resource expects forward slashes
        tileset_path = tileset_path.replace('\\', '/')
        return tileset.get_tileset(tileset_path)
