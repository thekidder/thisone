import logging

import pyglet.image

import game.imagecache


logger = logging.getLogger(__name__)

all = {
    'girl_walk_right' : [
        (0.25, 'girl_walk_right_1'),
        (0.25, 'girl_walk_right_2'),
        (0.25, 'girl_walk_right_3'),
        (0.25, 'girl_walk_right_4')],
    'girl_walk_left' : [
        (0.25, 'girl_walk_left_1'),
        (0.25, 'girl_walk_left_2'),
        (0.25, 'girl_walk_left_3'),
        (0.25, 'girl_walk_left_4') ],
    'girl_walk_top' : [
        (0.25, 'girl_walk_top_1'),
        (0.25, 'girl_walk_top_2'),
        (0.25, 'girl_walk_top_3'),
        (0.25, 'girl_walk_top_4') ],
    'girl_walk_bottom' : [
        (0.25, 'girl_walk_bottom_1'),
        (0.25, 'girl_walk_bottom_2'),
        (0.25, 'girl_walk_bottom_3'),
        (0.25, 'girl_walk_bottom_4') ],
    'girl_idle' : [
        (0.25, 'girl_idle_1'),
        (0.25, 'girl_idle_2'),
        (0.25, 'girl_idle_3'),
        (0.25, 'girl_idle_4') ],
    }


def get_animation(name):
    a = all[name]

    frames = list()

    for f in a:
        duration,img = f
        frames.append(pyglet.image.AnimationFrame(game.imagecache.get_sprite(img), duration))

    animation = pyglet.image.Animation(frames)

    return animation
