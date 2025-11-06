import pygame as pg
import math

class Bullet:
    def __init__(self, x, y, direction, speed=8, damage=10, radius=5):
        self.x = x
        self.y = y
        self.direction = direction  # 角度（度）
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.color = (255, 255, 0)  # 黄色
        self.active = True
        self.lifetime = 180  # 子弹存在时间（帧）
        self.timer = 0
    
    def update(self, screen_width, screen_height):
        """更新子弹位置和状态"""
        # 移动
        rad = math.radians(self.direction)
        self.x += math.cos(rad) * self.speed
        self.y -= math.sin(rad) * self.speed
        
        # 生命周期
        self.timer += 1
        if self.timer >= self.lifetime:
            self.active = False
        
        # 边界检测
        if (self.x < 0 or self.x > screen_width or 
            self.y < 0 or self.y > screen_height):
            self.active = False
    
    def draw(self, screen):
        """绘制子弹"""
        if self.active:
            pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
    
    def get_rect(self):
        """获取碰撞矩形"""
        return pg.Rect(self.x - self.radius, self.y - self.radius, 
                      self.radius * 2, self.radius * 2)