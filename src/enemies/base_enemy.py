import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, hp, speed, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = hp
        self.speed = speed

    def update(self, player):
        """所有敌人共有的逻辑写这里（比如朝玩家移动）"""
        pass
