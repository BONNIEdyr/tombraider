from .base_enemy import Enemy
import pygame as pg

class Slime(Enemy):
    def __init__(self, x, y):
        slime_image = pg.image.load("assets/enemies/slime.png").convert_alpha()
        super().__init__(x, y, hp=50, speed=2, image=slime_image)

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