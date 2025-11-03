from .base_enemy import Enemy
import pygame as pg

SCALE_FACTOR = 0.4

class Slime(Enemy):
    """
    史莱姆敌人类
    """
    def __init__(self, x, y):
        original_image = pg.image.load("assets/enemies/mummy.png").convert_alpha()
        
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        slime_image = pg.transform.scale(original_image, (new_w, new_h))
        super().__init__(x, y, hp=50, speed=0.5, image=slime_image)

    def update(self, player):
        """史莱姆的特定逻辑"""
        if player.rect.x < self.rect.x:
            self.rect.x -= self.speed
        elif player.rect.x > self.rect.x:
            self.rect.x += self.speed

        if player.rect.y < self.rect.y:
            self.rect.y -= self.speed
        elif player.rect.y > self.rect.y:
            self.rect.y += self.speed