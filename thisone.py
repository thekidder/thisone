#!/usr/bin/env python
import logging
import sys

import pyglet

import game
import kidgine.config
import kidgine.renderer
import kidgine.utils


logger = logging.getLogger()

sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

logger.setLevel(logging.DEBUG)

PROFILE = False

def create_cvars():
    c = kidgine.config.Config()

    c.add('cl_fullscreen',         kidgine.renderer.FullscreenVar(False))
    c.add('cl_screen_width',       kidgine.renderer.WidthVar(1280))
    c.add('cl_screen_height',      kidgine.renderer.HeightVar(720))
    c.add('cl_vsync',              kidgine.renderer.VsyncVar(True))

    return c


def main():
    kidgine.utils.add_file_logger('this_one', 'client')

    configs = kidgine.config.GameConfigs(None, create_cvars())

    g = game.Game(configs)
    pyglet.app.run()


if __name__ == '__main__':
    if PROFILE or '--profile' in sys.argv:
        import cProfile
        cProfile.run('main()', '.cprofile')
    else:
        main()
