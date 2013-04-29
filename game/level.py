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

                flipped = tile & tileset.FLIP_MASK
                tile = tile & ~tileset.FLIP_MASK

                x = i % width
                y = height - i / width

                img = tiles.get(tile)

                flip_x = flipped & tileset.FLIPPED_HORIZONTAL
                flip_y = flipped & tileset.FLIPPED_VERTICAL

                if flipped & tileset.FLIPPED_DIAGONAL:
                    if (flipped & tileset.FLIPPED_HORIZONTAL) and not (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = 90
                        flip_x = False
                    elif not (flipped & tileset.FLIPPED_HORIZONTAL) and (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = -90
                        flip_y = False
                    elif not (flipped & tileset.FLIPPED_HORIZONTAL) and not (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = -90
                        flip_x = True
                    else:
                        rotation = 90
                        flip_y = False
                else:
                    rotation = 0
                img = img.get_transform(
                    flip_x = flip_x,
                    flip_y = flip_y,
                    rotate = rotation)

                s = pyglet.sprite.Sprite(img, batch=self.batch)
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
