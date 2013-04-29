import data.tilesets
import kidgine.resource


_all_tilesets = dict()

FLIPPED_HORIZONTAL = 1 << 31
FLIPPED_VERTICAL   = 1 << 30
FLIPPED_DIAGONAL   = 1 << 29

FLIP_MASK = (FLIPPED_HORIZONTAL | FLIPPED_VERTICAL | FLIPPED_DIAGONAL)

def get_tileset(filename):
    if filename not in _all_tilesets:
        _all_tilesets[filename] = Tileset(filename)

    return _all_tilesets[filename]


class Tileset(object):
    tile_width = 32
    tile_height = 32

    def __init__(self, filename):
        self.images = dict()
        self.collidables = data.tilesets.all[filename]

        image = kidgine.resource.load_texture(filename)

        width = image.width / self.tile_width
        height = image.height / self.tile_height

        for i in xrange(width):
            for j in xrange(height):
                self.images[i + j*width+1] = image.get_region(
                    i * self.tile_width,
                    image.height - ((j + 1) * self.tile_height),
                    self.tile_width,
                    self.tile_height)
                self.images[i + j*width+1].anchor_x = 16
                self.images[i + j*width+1].anchor_y = 16


    def get(self, offset):
        return self.images[offset]


    def collides(self, offset):
        offset = offset & ~FLIP_MASK
        return offset in self.collidables
