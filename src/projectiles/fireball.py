import pygame as pg
import math


class Fireball(pg.sprite.Sprite):
    """
    魔法师发射的投射物类
    """
    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__()

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

    def update(self):
        """
        更新火球的位置和生命周期。
        """
        self.x += self.vel_x
        self.y += self.vel_y

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        self.timer += 1

        if self.timer >= self.lifetime:
            self.kill() 

    def hit_player(self, player):
        """
        当火球击中玩家时调用的方法。
        :param player: 玩家对象
        :return: 造成的伤害值
        """
        self.kill()
        return self.damage