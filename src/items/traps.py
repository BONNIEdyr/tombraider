import pygame as pg
from .base_item import Item

class FallingRocksTrap(Item):
    def __init__(self):
        super().__init__("Falling Rocks Trap", "common", "assets/items/rocks_trap.png")
        self.activated = False
        self.activation_timer = 0
    
    def apply_effect(self, player):
        """Damage player when trap is triggered"""
        if not self.activated:
            damage = player.health_system.max_health * 0.4
            player.take_damage(damage)
            self.activated = True
            self.activation_timer = 60
            return f"触发了落石陷阱！受到{damage}点伤害"
        return
    
    def draw(self, screen):
        """Draw trap with red color when activated"""
        if self.activated and self.activation_timer > 0:
            pg.draw.circle(screen, (255, 0, 0), self.position, 15)
            self.activation_timer -= 1
        else:
            super().draw(screen)
    
    def update(self):
        """Update trap activation timer"""
        if self.activated and self.activation_timer > 0:
            self.activation_timer -= 1
