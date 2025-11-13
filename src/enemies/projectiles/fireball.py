import pygame as pg
import math


class Fireball(pg.sprite.Sprite):
    # This class represents a projectile fired by the wizard.
    def __init__(self, start_x, start_y, target_x, target_y):
        # Initialize the fireball with position, velocity, and appearance.
        super().__init__()

        try:
            raw = pg.image.load("assets/fireball.png").convert_alpha()
            size = int(16 * 2.5)
            self.image = pg.transform.scale(raw, (size, size))
        except Exception:
            self.image = pg.Surface((16, 16), pg.SRCALPHA)
            pg.draw.circle(self.image, (255, 100, 0), (8, 8), 8)

        self.rect = self.image.get_rect(center=(start_x, start_y))

        self.speed = 5.0
        self.damage = 10
        self.lifetime = 180
        self.timer = 0

        self.x = float(start_x)
        self.y = float(start_y)

        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)

        if distance > 0:
            self.vel_x = (dx / distance) * self.speed
            self.vel_y = (dy / distance) * self.speed
        else:
            self.vel_x, self.vel_y = 0.0, 0.0

    # This function updates the fireball position and lifetime.
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        self.timer += 1

        if self.timer >= self.lifetime:
            self.kill()

    # This function handles collision with the player and returns damage value.
    def hit_player(self, player):
        self.kill()
        return self.damage
