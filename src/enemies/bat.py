import pygame as pg
from .base_enemy import Enemy

class Bat(Enemy):
    """
    蝙蝠敌人类
    """
    def __init__(self, x, y):
        bat_image = pg.image.load("assets/enemies/bat.png").convert_alpha()
        super().__init__(x, y, hp=30, speed=3, image=bat_image)

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