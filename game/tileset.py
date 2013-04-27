import kidgine.resource


_all_tilesets = dict()

def get_tileset(filename):
    if filename not in _all_tilesets:
        _all_tilesets[filename] = Tileset(filename)

    return _all_tilesets[filename]


class Tileset(object):
    tile_width = 32
    tile_height = 32

    def __init__(self, filename):
        self.images = dict()

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


    def get(self, offset):
        return self.images[offset]
