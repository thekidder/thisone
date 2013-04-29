import json
import logging
import os.path

import pyglet.graphics
import pyglet.sprite

import kidgine.collision.rectangle
import kidgine.collision.shape
import kidgine.utils
import tileset
from kidgine.math.vector import Vector
from collision import Tags
import renderable


logger = logging.getLogger(__name__)

class Level(object):
    def __init__(self, filename, collision_detector):
        with open(filename) as f:
            json_level = json.load(f)

        tiles = _get_tileset(filename, json_level['tilesets'][0]['image'])

        width  = json_level['layers'][0]['width']
        height = json_level['layers'][0]['height']

        self.filename = filename

        for layer in json_level['layers']:
            if not layer['visible']:
                continue
            for i,tile in enumerate(layer['data']):
                if tile == 0:
                    continue

                tile = tile & ~tileset.FLIP_MASK

                if not tiles.collides(tile):
                    continue

                x = 32 * (i % width)
                y = 32 * (height - i / width)

                center = Vector(x + 16, y + 16)
                tl = Vector(-16, -16)
                br = Vector(16, 16)

                token = '{}_{}_{}'.format(filename, x, y)
                c = kidgine.collision.rectangle.Rectangle(None, tl, br, center = center)
                c.tags = set([kidgine.collision.shape.tags.IMPEEDS_MOVEMENT, Tags.ENVIRONMENT])
                collision_detector.update_collidable(token, c)


    def update(self, t, dt, collision_detector):
        pass


    def alive(self):
        return True


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.LevelRenderable(self.filename, batch, group)
        return wrapped


def _get_tileset(filename, path):
        tileset_path = os.path.join(os.path.dirname(filename), path)
        tileset_path = os.path.normcase(os.path.normpath(tileset_path))
        # this is hacky: pyglet.resource expects forward slashes
        tileset_path = tileset_path.replace('\\', '/')
        return tileset.get_tileset(tileset_path)
