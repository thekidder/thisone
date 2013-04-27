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
    'girl_walk_right_1'   : ('data/images/girl/girl_walk_right.png',   0,    0,   32, 48, 16,  0),
    'girl_walk_right_2'   : ('data/images/girl/girl_walk_right.png',  32,    0,   32, 48, 16,  0),
    'girl_walk_right_3'   : ('data/images/girl/girl_walk_right.png',  64,    0,   32, 48, 16,  0),
    'girl_walk_right_4'   : ('data/images/girl/girl_walk_right.png',  96,    0,   32, 48, 16,  0),
    'girl_walk_left_4'    : ('data/images/girl/girl_walk_left.png',    0,    0,   32, 48, 16,  0),
    'girl_walk_left_3'    : ('data/images/girl/girl_walk_left.png',   32,    0,   32, 48, 16,  0),
    'girl_walk_left_2'    : ('data/images/girl/girl_walk_left.png',   64,    0,   32, 48, 16,  0),
    'girl_walk_left_1'    : ('data/images/girl/girl_walk_left.png',   96,    0,   32, 48, 16,  0),
    'girl_walk_top_1'     : ('data/images/girl/girl_walk_top.gif',     0,    0,   32, 48, 16,  0),
    'girl_walk_top_2'     : ('data/images/girl/girl_walk_top.gif',    32,    0,   32, 48, 16,  0),
    'girl_walk_top_3'     : ('data/images/girl/girl_walk_top.gif',    64,    0,   32, 48, 16,  0),
    'girl_walk_top_4'     : ('data/images/girl/girl_walk_top.gif',    96,    0,   32, 48, 16,  0),
    'girl_walk_bottom_1'  : ('data/images/girl/girl_walk_bottom.gif',  0,    0,   32, 48, 16,  0),
    'girl_walk_bottom_2'  : ('data/images/girl/girl_walk_bottom.gif', 32,    0,   32, 48, 16,  0),
    'girl_walk_bottom_3'  : ('data/images/girl/girl_walk_bottom.gif', 64,    0,   32, 48, 16,  0),
    'girl_walk_bottom_4'  : ('data/images/girl/girl_walk_bottom.gif', 96,    0,   32, 48, 16,  0),


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
