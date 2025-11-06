# [file name]: src/items/traps.py
# [file content begin]
import pygame as pg
from .base_item import Item

class FallingRocksTrap(Item):
    """落石陷阱 - 造成40%最大生命值的伤害"""
    def __init__(self):
        super().__init__("Falling Rocks Trap", "common", "assets/items/rocks_trap.png")
        self.activated = False
        self.activation_timer = 0
    
    def apply_effect(self, player):
        """陷阱被触发时的效果"""
        if not self.activated:
            damage = player.health_system.max_health * 0.4
            player.take_damage(damage)
            self.activated = True
            self.activation_timer = 60  # 1秒的激活状态显示
            return f"触发了落石陷阱！受到{damage}点伤害"
        return
    
    def draw(self, screen):
        """绘制陷阱（激活状态显示红色）"""
        if self.activated and self.activation_timer > 0:
            # 激活状态显示为红色
            pg.draw.circle(screen, (255, 0, 0), self.position, 15)
            self.activation_timer -= 1
        else:
            super().draw(screen)
    
    def update(self):
        """更新陷阱状态"""
        if self.activated and self.activation_timer > 0:
            self.activation_timer -= 1
# [file content end]