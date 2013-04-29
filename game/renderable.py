import json
import logging

import pyglet.graphics
import pyglet.sprite
import pyglet.text
from pyglet.gl import *

import dialog
import imagecache
import level
import sprite
import tileset
import utils


logger = logging.getLogger(__name__)

class LevelRenderable(object):
    tile_width = 32
    tile_height = 32

    def __init__(self, filename, batch, group):
        with open(filename) as f:
            json_level = json.load(f)

        tiles = level._get_tileset(filename, json_level['tilesets'][0]['image'])
        self.batch = batch
        self.group = pyglet.graphics.OrderedGroup(0, group)
        self.sprites = list()

        width  = json_level['layers'][0]['width']
        height = json_level['layers'][0]['height']
        for layer in json_level['layers']:
            if not layer['visible']:
                continue
            for i,tile in enumerate(layer['data']):
                if tile == 0:
                    continue

                flipped = tile & tileset.FLIP_MASK
                tile = tile & ~tileset.FLIP_MASK

                x = i % width
                y = height - i / width

                #print 'loaded {} at {},{} with flippd {}'.format(tile,x,y,flipped)

                img = tiles.get(tile)

                flip_x = flipped & tileset.FLIPPED_HORIZONTAL
                flip_y = flipped & tileset.FLIPPED_VERTICAL

                if flipped & tileset.FLIPPED_DIAGONAL:
                    if (flipped & tileset.FLIPPED_HORIZONTAL) and not (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = 90
                        flip_x = False
                    elif not (flipped & tileset.FLIPPED_HORIZONTAL) and (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = -90
                        flip_y = False
                    elif not (flipped & tileset.FLIPPED_HORIZONTAL) and not (flipped & tileset.FLIPPED_VERTICAL):
                        rotation = -90
                        flip_x = True
                    else:
                        rotation = 90
                        flip_y = False
                else:
                    rotation = 0
                img = img.get_transform(
                    flip_x = flip_x,
                    flip_y = flip_y,
                    rotate = rotation)

                img.anchor_x = 0
                img.anchor_y = 0

                s = pyglet.sprite.Sprite(img, batch=self.batch,group=self.group)
                s.x = x * self.tile_width
                s.y = y * self.tile_height
                self.sprites.append(s)


    def update(self, t, dt):
        pass


class StaticSpriteRenderable(object):
    def __init__(self, batch, group, parent, image, rotation = 0, order = 5):
        group = pyglet.graphics.OrderedGroup(order, group)
        self.sprite = pyglet.sprite.Sprite(imagecache.get_sprite(image), batch = batch, group = group)
        self.sprite.rotation = rotation
        self.parent = parent


    def update(self, t, dt):
        utils.set_sprite_pos(self.sprite, self.parent.position)


    def delete(self):
        self.sprite.delete()


class OpacityFaderRenderable(object):
    def __init__(self, batch, group, obj):
        self.obj = obj
        self.batch = batch
        self.rect = None


    def update(self, t, dt, window):
        self.delete()

        opacity = self.obj.opacity
        self.rect = self.batch.add(
            4,
            GL_QUADS,
            None,
            ('v2f', (0.0, 0.0,
                     0.0, window.height,
                     window.width, window.height,
                     window.width, 0.0)),
            ('c4f', (self.obj.r, self.obj.g, self.obj.b, opacity) * 4))


    def delete(self):
        if self.rect:
            self.rect.delete()


class DialogRenderable(object):
    def __init__(self, batch, group, dialog):
        self.batch = batch
        self.group = group

        self.dialog = dialog

        self.dialog_background = pyglet.sprite.Sprite(
            imagecache.get_sprite('dialog_bg'),
            batch = batch,
            group = pyglet.graphics.OrderedGroup(0, self.group))
        self.dialog_name_background = pyglet.sprite.Sprite(
            imagecache.get_sprite('dialog_name_bg'),
            batch = batch,
            group = pyglet.graphics.OrderedGroup(1, self.group))
        self.dialog_next = pyglet.sprite.Sprite(
            imagecache.get_sprite('dialog_next'),
            batch = batch,
            group = pyglet.graphics.OrderedGroup(2, self.group))

        self.text = None
        self.name_text = None

        self.new_text()


    def new_text(self):
        if self.name_text:
            self.name_text.delete()
        if self.text:
            self.text.delete()

        self.name_text = pyglet.text.HTMLLabel(
            text = self.dialog.get_current_line()['name'],
            batch = self.batch,
            group = pyglet.graphics.OrderedGroup(10, self.group))
        self.text = pyglet.text.HTMLLabel(
            text = self.dialog.get_current_line()['dialog'],
            width = 800,
            multiline = True,
            batch = self.batch,
            group = pyglet.graphics.OrderedGroup(10, self.group))
        self.set_style(self.name_text)
        self.set_style(self.text)

        self.name_text.set_style('font_size', 24)
        self.text.set_style('font_size', 18)


    def set_style(self, text):
        text.set_style('font_name', 'Courier New')
        text.set_style('color', (0, 0, 0, 255))


    # assumes rendering in screen space
    def update(self, t, dt, window):
        self.dialog_background.x = (window.width - self.dialog_background.width) / 2
        self.dialog_background.y = 40

        self.dialog_name_background.x = (window.width - self.dialog_background.width) / 2 - 20
        if self.dialog.get_current_line()['portrait_facing'] == dialog.PortraitFacing.right:
            self.dialog_name_background.x = (window.width
                                             - self.dialog_name_background.x
                                             - self.dialog_name_background.width)
        self.dialog_name_background.y = 220

        self.dialog_next.x = window.width - (window.width - self.dialog_background.width) / 2 - 120
        self.dialog_next.y = 60

        if self.dialog.can_transition(t):
            self.dialog_next.visible = True
        else:
            self.dialog_next.visible = False

        if self.name_text:
            self.name_text.x = self.dialog_name_background.x + 20
            self.name_text.y = 240

        if self.text:
            self.text.x = self.dialog_background.x + 20
            self.text.y = 180


    def delete(self):
        self.dialog_background.delete()
        self.dialog_name_background.delete()
        self.dialog_next.delete()

        if self.text:
            self.text.delete()
        if self.name_text:
            self.name_text.delete()


class CharacterRenderable(object):
    def __init__(self, batch, group, character, sprite_base):
        group = pyglet.graphics.OrderedGroup(10, group)

        self.character = character
        self.last_sprite_index = 0

        self.sprites = list()
        # 0-3 : left,right,top,bottom
        # 4-7 : walk; left,right,top,bottom
        # 8   : idle

        # stationary
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_left'),
                                                 batch = batch,
                                                 group = group))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_right'),
                                                 batch = batch,
                                                 group = group))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_top'),
                                                 batch = batch,
                                                 group = group))
        self.sprites.append(pyglet.sprite.Sprite(imagecache.get_sprite(sprite_base + '_bottom'),
                                                 batch = batch,
                                                 group = group))

        # walk
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_left'),
                                                  batch = batch,
                                                  group = group))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_right'),
                                                  batch = batch,
                                                  group = group))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_top'),
                                                  batch = batch,
                                                  group = group))
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_walk_bottom'),
                                                  batch = batch,
                                                  group = group))

        #idle
        self.sprites.append(sprite.AnimatedSprite(imagecache.get_animation(sprite_base + '_idle'),
                                                  batch = batch,
                                                  group = group))


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
    def __init__(self, batch, group, character):
        super(MeleeEnemyRenderable, self).__init__(batch, group, character, self.sprite_name)
        self.blinker = BlinkOnDamage(self)


    def update(self, t, dt):
        super(MeleeEnemyRenderable, self).update(t, dt)
        self.blinker.update(t, dt)


class GirlRenderable(CharacterRenderable):
    sprite_name = 'girl'
    def __init__(self, batch, group, character):
        super(GirlRenderable, self).__init__(batch, group, character, self.sprite_name)
        self.blinker = BlinkOnDamage(self)


    def update(self, t, dt):
        super(GirlRenderable, self).update(t, dt)
        self.blinker.update(t, dt)
