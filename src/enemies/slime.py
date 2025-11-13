from .base_enemy import Enemy
import pygame as pg

SCALE_FACTOR = 0.4

class Slime(Enemy):
    # Enemy that slowly follows the player.
    def __init__(self, x, y):
        # Initialize the slime with scaled image and basic stats.
        original_image = pg.image.load("assets/enemies/mummy.png").convert_alpha()
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        slime_image = pg.transform.scale(original_image, (new_w, new_h))
        super().__init__(x, y, hp=50, speed=0.5, image=slime_image)

    def update(self, player):
        # Update slime behavior: move slowly toward the player.
        if player.rect.x < self.rect.x:
            self.rect.x -= self.speed
        elif player.rect.x > self.rect.x:
            self.rect.x += self.speed

        if player.rect.y < self.rect.y:
            self.rect.y -= self.speed
        elif player.rect.y > self.rect.y:
            self.rect.y += self.speed
