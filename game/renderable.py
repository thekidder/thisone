import pyglet.sprite

import imagecache
import sprite
import utils


class StaticSpriteRenderable(object):
    def __init__(self, batch, parent, image):
        self.sprite = pyglet.sprite.Sprite(imagecache.get_sprite(image), batch = batch)
        self.parent = parent


    def update(self):
        utils.set_sprite_pos(self.sprite, self.parent.position)



class CharacterRenderable(object):
    def __init__(self, batch, character, sprite_base):
        self.character = character
        self.last_sprite_index = 0

        self.sprites = list()
        # 0-3 : left,right,top,bottom
        # 4-7 : walk; left,right,top,bottom
        # 8   : idle

        # stationary
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_left'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_right'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_top'), batch = batch))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_bottom'), batch = batch))

        # walk
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_left'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_right'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_top'),
                                                  batch = batch))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_bottom'),
                                                  batch = batch))

        #idle
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_idle'), batch = batch))


    def update(self, t, dt):
        if self.character.idle:
            used_sprite_index = 8
        else:
            used_sprite_index = self.character.facing
            if self.character.moving:
                used_sprite_index += 4

        if used_sprite_index != self.last_sprite_index:
            new = self.sprites[used_sprite_index]
            if isinstance(new, sprite.AnimatedSprite):
                new.set_frame(0)
                new.play()

            self.last_sprite_index = used_sprite_index

        for i,s in enumerate(self.sprites):
            s.visible = (used_sprite_index == i)

        utils.set_sprite_pos(self.sprites[used_sprite_index], self.character.position)


    def delete(self):
        for i in self.sprites:
            i.delete()


class BlinkOnDamage(object):
    def __init__(self, parent):
        self.last_blink = 0
        self.frame = 0
        self.parent = parent


    def update(self, t, dt):
        if self.parent.character.max_health - self.parent.character.health < 10.1:
            self.frame = 0
        else:
            self.last_blink += dt

            blink_time = 0.4 * (1.0 - (self.parent.character.max_health - self.parent.character.health) /
                                self.parent.character.max_health)

            if self.last_blink > blink_time:
                self.last_blink = 0
                self.frame += 1
                if self.frame == 2:
                    self.frame = 0

        if self.frame == 1:
            self.parent.sprites[self.parent.last_sprite_index].color = (255, 128, 128)
        else:
            self.parent.sprites[self.parent.last_sprite_index].color = (255, 255, 255)


class MeleeEnemyRenderable(CharacterRenderable):
    sprite_name = 'enemy_1'
    def __init__(self, batch, character):
        super(MeleeEnemyRenderable, self).__init__(batch, character, self.sprite_name)
        self.blinker = BlinkOnDamage(self)


    def update(self, t, dt):
        super(MeleeEnemyRenderable, self).update(t, dt)
        self.blinker.update(t, dt)


class GirlRenderable(CharacterRenderable):
    sprite_name = 'girl'
    def __init__(self, batch, character):
        super(GirlRenderable, self).__init__(batch, character, self.sprite_name)
        self.blinker = BlinkOnDamage(self)


    def update(self, t, dt):
        super(GirlRenderable, self).update(t, dt)
        self.blinker.update(t, dt)
