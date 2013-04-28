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

    #   name                spritesheet                                 x     y    w   h   a_x  a_y
    'test_left'           : ('data/images/test_left.png',               0,    0,   32, 32, 16,  0),
    'test_right'          : ('data/images/test_right.png',              0,    0,   32, 32, 16,  0),
    'test_top'            : ('data/images/test_top.png',                0,    0,   32, 32, 16,  0),
    'test_bottom'         : ('data/images/test_bottom.png',             0,    0,   32, 32, 16,  0),
    'test_walk_left'      : ('data/images/test_left.png',               0,    0,   32, 32, 16,  0),
    'test_walk_right'     : ('data/images/test_right.png',              0,    0,   32, 32, 16,  0),
    'test_walk_top'       : ('data/images/test_top.png',                0,    0,   32, 32, 16,  0),
    'test_walk_bottom'    : ('data/images/test_bottom.png',             0,    0,   32, 32, 16,  0),
    'test_idle'           : ('data/images/test_bottom.png',             0,    0,   32, 32, 16,  0),

    'girl_left'           : ('data/images/girl/girl_left.png',          0,    0,   32, 48, 16,  0),
    'girl_right'          : ('data/images/girl/girl_right.png',         0,    0,   32, 48, 16,  0),
    'girl_top'            : ('data/images/girl/girl_top.png',           0,    0,   32, 48, 16,  0),
    'girl_bottom'         : ('data/images/girl/girl_bottom.png',        0,    0,   32, 48, 16,  0),
    'girl_walk_right'     : ('data/images/girl/girl_walk_right.png',    0,    0,  128, 48,  0,  0),
    'girl_walk_left'      : ('data/images/girl/girl_walk_left.png',     0,    0,  128, 48,  0,  0),
    'girl_walk_top'       : ('data/images/girl/girl_walk_top.png',      0,    0,   64, 48,  0,  0),
    'girl_walk_bottom'    : ('data/images/girl/girl_walk_bottom.png',   0,    0,   64, 48,  0,  0),
    'girl_idle'           : ('data/images/girl/girl_idle.png',          0,    0,  416, 48,  0,  0),

    'enemy_1_left'        : ('data/images/derp/enemy_1_walk_left.png',  0,    0,   24, 33, 12,  0),
    'enemy_1_right'       : ('data/images/derp/enemy_1_walk_right.png', 0,    0,   24, 33, 12,  0),
    'enemy_1_top'         : ('data/images/derp/enemy_1_walk_top.png',   0,    0,   15, 33,  7,  0),
    'enemy_1_bottom'      : ('data/images/derp/enemy_1_walk_bottom.png',0,    0,   15, 33,  7,  0),
    'enemy_1_walk_right'  : ('data/images/derp/enemy_1_walk_right.png', 0,    0,   96, 33,  0,  0),
    'enemy_1_walk_left'   : ('data/images/derp/enemy_1_walk_left.png',  0,    0,   96, 33,  0,  0),
    'enemy_1_walk_top'    : ('data/images/derp/enemy_1_walk_top.png',   0,    0,   60, 33,  0,  0),
    'enemy_1_walk_bottom' : ('data/images/derp/enemy_1_walk_bottom.png',0,    0,   60, 33,  0,  0),
    'enemy_1_idle'        : ('data/images/derp/enemy_1_idle.png',       0,    0,   30, 33,  0,  0),
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
