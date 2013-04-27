import kidgine.resource

__all_sprites = {
    # format is the following:
    # key:
    #   x   = x coord in spritesheet
    #   y   = y coord in spritesheet
    #   w   = width of sprite
    #   h   = height of sprite
    #   a_x = x coordinate of anchor (from bottom left of sprite)
    #   a_y = y coordinate of anchor

    #   name                spritesheet                                x     y    w   h   a_x  a_y
    'girl_left'           : ('data/images/girl/girl_left.png',         0,    0,   32, 48, 16,  0),
    'girl_right'          : ('data/images/girl/girl_right.png',        0,    0,   32, 48, 16,  0),
    'girl_top'            : ('data/images/girl/girl_top.png',          0,    0,   32, 48, 16,  0),
    'girl_bottom'         : ('data/images/girl/girl_bottom.png',       0,    0,   32, 48, 16,  0),
    'girl_walk_right'     : ('data/images/girl/girl_walk_right.png',   0,    0,  128, 48,  0,  0),
    'girl_walk_left'      : ('data/images/girl/girl_walk_left.png',    0,    0,  128, 48,  0,  0),
    'girl_walk_top'       : ('data/images/girl/girl_walk_top.gif',     0,    0,  128, 48,  0,  0),
    'girl_walk_bottom'    : ('data/images/girl/girl_walk_bottom.gif',  0,    0,  128, 48,  0,  0),
    'girl_idle'           : ('data/images/girl/girl_idle.png',         0,    0,  416, 48,  0,  0),
}


def get_sprite(name):
    return kidgine.resource.load_from_spritesheet(
        __all_sprites[name][0],
        __all_sprites[name][1],
        __all_sprites[name][2],
        __all_sprites[name][3],
        __all_sprites[name][4],
        __all_sprites[name][5],
        __all_sprites[name][6])
