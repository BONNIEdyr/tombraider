import pygame as pg
from .base_enemy import Enemy

SCALE_FACTOR = 0.2

class Bat(Enemy):
    # This class defines a bat enemy that tracks the player.
    TRANSPARENT_COLOR = (255, 255, 255)

    # This function initializes the bat enemy with scaled image and base attributes.
    def __init__(self, x, y):
        original_image = pg.image.load("assets/enemies/bat.png").convert()
        original_image.set_colorkey(self.TRANSPARENT_COLOR)
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        bat_image = pg.transform.scale(original_image, (new_w, new_h))
        super().__init__(x, y, hp=30, speed=1, image=bat_image)

    # This function defines the bat's specific logic to follow the player.
    def update(self, player):
        bat_center_x = self.rect.centerx
        bat_center_y = self.rect.centery
        player_center_x = player.rect.centerx
        player_center_y = player.rect.centery

        if player_center_x < bat_center_x:
            self.rect.x -= self.speed
        elif player_center_x > bat_center_x:
            self.rect.x += self.speed

        if player_center_y < bat_center_y:
            self.rect.y -= self.speed
        elif player_center_y > bat_center_y:
            self.rect.y += self.speed
