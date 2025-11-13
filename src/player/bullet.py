import pygame as pg
import math

_bullet_raw = None


class Bullet:
    def __init__(self, x, y, direction, speed=8, damage=10, radius=5):
        """Initialize a bullet with position, direction, speed, damage and radius"""
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.color = (255, 255, 0)
        self.active = True
        self.lifetime = 180
        self.timer = 0
    
    def update(self, screen_width, screen_height):
        """Update bullet position, lifetime and check boundaries"""
        rad = math.radians(self.direction)
        self.x += math.cos(rad) * self.speed
        self.y -= math.sin(rad) * self.speed
        
        self.timer += 1
        if self.timer >= self.lifetime:
            self.active = False
        
        if (self.x < 0 or self.x > screen_width or 
            self.y < 0 or self.y > screen_height):
            self.active = False
    
    def draw(self, screen):
        """Draw the bullet on the screen using image or circle"""
        if self.active:
            global _bullet_raw
            if _bullet_raw is None:
                try:
                    _bullet_raw = pg.image.load("assets/bullet.png")
                except Exception:
                    _bullet_raw = None

            if _bullet_raw is not None:
                try:
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
        """Get the collision rectangle for the bullet"""
        return pg.Rect(self.x - self.radius, self.y - self.radius, 
                      self.radius * 2, self.radius * 2)