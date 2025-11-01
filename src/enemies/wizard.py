from .base_enemy import Enemy
import pygame as pg
import math
from .projectiles.fireball import Fireball

ATTACK_COOLDOWN = 120 
SCALE_FACTOR = 0.2

class Wizard(Enemy):
    """
    魔法师敌人类，继承自 Enemy。
    它会保持距离，并周期性地发射投射物 (Fireball)
    """
    TRANSPARENT_COLOR = (255, 255, 255)
    def __init__(self, x, y):
        original_image = pg.image.load("assets/enemies/wizard.png").convert()
        original_image.set_colorkey(self.TRANSPARENT_COLOR)
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        wizard_image = pg.transform.scale(original_image, (new_w, new_h))
        super().__init__(x, y, hp=75, speed=0.5, image=wizard_image)
        
        self.attack_timer = 0
        self.attack_range = 300 

    def update(self, player):
        """
        魔法师的特定逻辑：
        1. 保持攻击计时器。
        2. 如果计时器准备好，且玩家在范围内，则发射火球。
        """
        
        new_projectile = None

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        self.attack_timer += 1

        if self.attack_timer >= ATTACK_COOLDOWN:
            if distance <= self.attack_range:

                new_projectile = Fireball(
                    self.rect.centerx, 
                    self.rect.centery, 
                    player.rect.centerx, 
                    player.rect.centery
                )
                
                self.attack_timer = 0

                if distance < 150:
                    self.rect.x -= int(self.speed * (dx / distance)) if distance > 0 else 0
                    self.rect.y -= int(self.speed * (dy / distance)) if distance > 0 else 0

        return new_projectile