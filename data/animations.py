import logging

import pyglet.image

import game.imagecache


logger = logging.getLogger(__name__)

all = {
    #   name               name of backing image  w   h   # frames duration of frames
    'girl_walk_right'   : ('girl_walk_right',     32, 48,  4,       0.25),
    'girl_walk_left'    : ('girl_walk_left',      32, 48,  4,       0.25),
    'girl_walk_top'     : ('girl_walk_top',       32, 48,  2,       0.25),
    'girl_walk_bottom'  : ('girl_walk_bottom',    32, 48,  2,       0.25),
    'girl_idle'         : ('girl_idle',           32, 48, 13,       0.04),
}


def animation_duration(name):
    img_name,width,height,num_frames,duration = all[name]

    return num_frames * duration


def get_animation(name):
    img_name,width,height,num_frames,duration = all[name]
    image = game.imagecache.get_sprite(img_name)

    frames = list()
    for i in xrange(num_frames):
        frame_img = image.get_region(i * width, 0, width, height)
        frame_img.anchor_x = width / 2
        frames.append(pyglet.image.AnimationFrame(frame_img, duration))

    animation = pyglet.image.Animation(frames)

    return animation
