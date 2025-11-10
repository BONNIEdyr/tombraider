import pygame as pg
import math

# 模块级缓存：延迟加载子弹图像（在 draw 时尝试），避免在模块导入时因 display 未初始化导致失败
_bullet_raw = None


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
            # 优先使用 bullet 图片（延迟加载以避免在 import 时出现 display 未初始化问题）
            global _bullet_raw
            if _bullet_raw is None:
                try:
                    _bullet_raw = pg.image.load("assets/bullet.png")
                except Exception:
                    _bullet_raw = None

            if _bullet_raw is not None:
                try:
                    # 将子弹图片缩放为原来直径的 2.5 倍
                    w = int(self.radius * 2 * 2.5)
                    h = int(self.radius * 2 * 2.5)
                    img = pg.transform.scale(_bullet_raw, (w, h))
                    rect = img.get_rect(center=(int(self.x), int(self.y)))
                    screen.blit(img, rect.topleft)
                    return
                except Exception:
                    pass
            pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
    
    def get_rect(self):
        """获取碰撞矩形"""
        return pg.Rect(self.x - self.radius, self.y - self.radius, 
                      self.radius * 2, self.radius * 2)