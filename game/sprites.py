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

    #   name                spritesheet                       x     y    w   h   a_x  a_y

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
