import pyglet
from pyglet.gl import *


def _fudge_tex_borders (fn):
    """takes a pyglet texture/region and insets the texture
    coordinates by half a texel allowing for sub-pixel blitting without
    interpolation with nearby regions within same texture atlas"""
    def wrapper(*args, **kwargs):
        tex = fn(*args, **kwargs)
        coord_width = tex.tex_coords[3] - tex.tex_coords[0]
        coord_height = tex.tex_coords[7] - tex.tex_coords[4]
        x_adjust = (coord_width / tex.width) / 2.0      # get tex coord half texel width
        y_adjust = (coord_height / tex.height) / 2.0    # get tex coord half texel width
        # create new 12-tuple texture coordinates
        tex.tex_coords = (
            tex.tex_coords[0 ] + x_adjust,
            tex.tex_coords[1 ] + y_adjust,
            tex.tex_coords[2 ],
            tex.tex_coords[3 ] - x_adjust,
            tex.tex_coords[4 ] + y_adjust,
            tex.tex_coords[5 ],
            tex.tex_coords[6 ] - x_adjust,
            tex.tex_coords[7 ] - y_adjust,
            tex.tex_coords[8 ],
            tex.tex_coords[9 ] + x_adjust,
            tex.tex_coords[10] - y_adjust,
            tex.tex_coords[11])
        return tex

    return wrapper


def load_from_spritesheet(path, x, y, width, height, anchor_x, anchor_y):
    img = _load_private(path, x, y, width, height)
    img.anchor_x = anchor_x
    img.anchor_y = anchor_y

    return img


def load_texture(path):
    file = pyglet.resource.file(path)
    img = pyglet.image.load(path, file, decoder=pyglet.image.codecs.pil.PILImageDecoder())
    tex =  img.get_texture()
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    return tex


def _load_private(path, x, y, width, height):
    img = load_texture(path)
    # index y from top of texture, not bottom
    #real_y = img.height - height - y
    img = img.get_region(x, y, width, height)
    return img
