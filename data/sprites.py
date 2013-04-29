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

    # characters
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

    'barbarian_left'        : ('data/images/barb/enemy_2.png',  0,    0,   37, 48, 12,  0),
    'barbarian_right'       : ('data/images/barb/enemy_2.png', 0,    0,   37, 48, 12,  0),
    'barbarian_top'         : ('data/images/barb/enemy_2.png',   0,    0,   37, 48, 12,  0),
    'barbarian_bottom'      : ('data/images/barb/enemy_2.png',0,    0,   37, 48, 12,  0),
    'barbarian_walk_right'  : ('data/images/barb/enemy_2.png', 0,    0,   37, 48, 12,  0),
    'barbarian_walk_left'   : ('data/images/barb/enemy_2.png',  0,    0,   37, 48, 12,  0),
    'barbarian_walk_top'    : ('data/images/barb/enemy_2.png',   0,    0,   37, 48, 12,  0),
    'barbarian_walk_bottom' : ('data/images/barb/enemy_2.png',0,    0,   37, 48, 12,  0),
    'barbarian_idle'        : ('data/images/barb/enemy_2.png',       0,    0,   37, 48, 12,  0),

    'warlord_left'        : ('data/images/bosses/warlord/boss-left.png',  0,    0,   41, 48, 12,  0),
    'warlord_right'       : ('data/images/bosses/warlord/boss-right.png', 0,    0,   41, 48, 12,  0),
    'warlord_top'         : ('data/images/bosses/warlord/boss-up.png',   0,    0,   41, 48, 12,  0),
    'warlord_bottom'      : ('data/images/bosses/warlord/boss.png',0,    0,   41, 48, 12,  0),
    'warlord_walk_right'  : ('data/images/bosses/warlord/boss-right.png', 0,    0,  207, 48, 0,  0),
    'warlord_walk_left'   : ('data/images/bosses/warlord/boss-left.png',  0,    0,  207, 48, 0,  0),
    'warlord_walk_top'    : ('data/images/bosses/warlord/boss-up.png',   0,    0,   205, 48, 0,  0),
    'warlord_walk_bottom' : ('data/images/bosses/warlord/boss.png',0,    0,  205, 48, 0,  0),
    'warlord_idle'        : ('data/images/bosses/warlord/boss.png',       0,    0,  205, 48, 0,  0),
    'warlord_spin'        : ('data/images/bosses/warlord/boss-spin.png',       0,    0,  328, 48, 0,  0),
    
    'hermit_left'           : ('data/images/hermit/hermit_left.png',          0,    0,   32, 48, 16,  0),
    'hermit_right'          : ('data/images/hermit/hermit_right.png',         0,    0,   32, 48, 16,  0),
    'hermit_top'            : ('data/images/hermit/hermit_top.png',           0,    0,   32, 48, 16,  0),
    'hermit_bottom'         : ('data/images/hermit/hermit_bottom.png',        0,    0,   32, 48, 16,  0),
    'hermit_idle'         : ('data/images/hermit/hermit_bottom.png',        0,    0,   32, 48, 16,  0),

    # attacks
    'fire_peak'           : ('data/images/fire_peak.png',               0,    0,   96, 96, 48, 48),
    'earth_peak'          : ('data/images/earth_peak.png',              0,    0,   96, 96, 48, 48),
    'wind_peak'           : ('data/images/wind_peak.png',              0,    0,   96, 96, 48, 48),
    'water_peak'          : ('data/images/water_peak.png',              0,    0,   96, 96, 48, 48),

    # projectiles
    'bomb'                : ('data/images/projectiles/bomb.png',          0,    0,   20, 15,  0,  0),
    'bomb_lit'            : ('data/images/projectiles/bomb-lit.png',      0,    0,   32, 32, 16, 16),
    'bomb_unlit'          : ('data/images/projectiles/bomb-unlit.png',    0,    0,   32, 32, 16, 16),
    'bomb_explosion'      : ('data/images/projectiles/bomb-explosion.png',0,    0,  160, 32,  0,  0),

    'spear'      : ('data/images/projectiles/spear.png',0,    0,  20, 20,  0,  0),

    # dialog system
    'dialog_bg'           : ('data/images/ui/dialog-box-1.png',            0,    0, 800,270,  0,  0),
    'dialog_name_bg'      : ('data/images/ui/dialog-box-2.png',       0,    0,  214, 57,  0,  0),
    'dialog_next'         : ('data/images/ui/dialog-box-3.png',          0,    0,   83, 47,  0,  0),

    # HUD
    'fire_hud'            : ('data/images/ui/elementbuttons.png',      0,    0,  24, 27,  0,  0),
    'water_hud'           : ('data/images/ui/elementbuttons.png',     24,    0,  24, 27,  0,  0),
    'wind_hud'            : ('data/images/ui/elementbuttons.png',     48,    0,  24, 27,  0,  0),
    'earth_hud'           : ('data/images/ui/elementbuttons.png',     72,    0,  24, 27,  0,  0),

    'fire_pressed_hud'    : ('data/images/ui/elementbuttons-pressed.png',  0,    0,  24, 27,  0,  0),
    'water_pressed_hud'   : ('data/images/ui/elementbuttons-pressed.png', 24,    0,  24, 27,  0,  0),
    'wind_pressed_hud'    : ('data/images/ui/elementbuttons-pressed.png', 48,    0,  24, 27,  0,  0),
    'earth_pressed_hud'   : ('data/images/ui/elementbuttons-pressed.png', 72,    0,  24, 27,  0,  0),

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
