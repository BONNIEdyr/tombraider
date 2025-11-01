import pygame as pg
from .base_enemy import Enemy

SCALE_FACTOR = 0.2

class Bat(Enemy):
    """
    蝙蝠敌人类
    """
    TRANSPARENT_COLOR = (255, 255, 255)
    def __init__(self, x, y):
        original_image = pg.image.load("assets/enemies/bat.png").convert()
        original_image.set_colorkey(self.TRANSPARENT_COLOR)
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        bat_image = pg.transform.scale(original_image, (new_w, new_h))
        super().__init__(x, y, hp=30, speed=1.5, image=bat_image)

    def update(self, player):
        """
        蝙蝠的特定逻辑：追踪玩家。
        """
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