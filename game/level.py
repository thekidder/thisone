import json
import logging
import os.path

import pyglet.graphics
import pyglet.sprite

import tileset


logger = logging.getLogger(__name__)

class Level(object):
    tile_width = 32
    tile_height = 32

    def __init__(self, filename):
        with open(filename) as f:
            json_level = json.load(f)

        tileset_path = os.path.join(os.path.dirname(filename), json_level['tilesets'][0]['image'])
        tileset_path = os.path.normcase(os.path.normpath(tileset_path))
        # this is hacky: pyglet.resource expects forward slashes
        tileset_path = tileset_path.replace('\\', '/')
        tiles = tileset.get_tileset(tileset_path)

        self.batch = pyglet.graphics.Batch()
        self.sprites = list()

        width  = json_level['layers'][0]['width']
        height = json_level['layers'][0]['height']
        for layer in json_level['layers']:
            for i,tile in enumerate(layer['data']):
                if tile == 0:
                    continue

                x = i % width
                y = i / width

                s = pyglet.sprite.Sprite(tiles.get(tile), batch=self.batch)
                s.x = x * self.tile_width
                s.y = y * self.tile_height
                self.sprites.append(s)


    def draw(self):
        self.batch.draw()
