from pyglet.gl import *


def screen_projection(window):
    ortho_projection(0, 0, window.width, window.height)


def ortho_projection(x, y, width, height):
    glMatrixMode(gl.GL_PROJECTION)
    glLoadIdentity()
    glOrtho(
        x,
        x + width,
        y + height,
        y,
        -1, 1)
    glMatrixMode(gl.GL_MODELVIEW)
