import pygame as pg
import math
from .health_system import HealthSystem
from .bullet import Bullet
from .constants import PLAYER_CONFIG, BULLET_CONFIG, CONTROLS

class Player:
    def __init__(self, x, y):
        # 基础属性
        self.x = x
        self.y = y
        self.radius = PLAYER_CONFIG["radius"]
        self.speed = PLAYER_CONFIG["speed"]
        self.color = PLAYER_CONFIG["color"]
        self.direction = 0  # 朝向角度
        
        # 系统组件
        self.health_system = HealthSystem(PLAYER_CONFIG["max_health"])
        self.bullets = []

        # 子弹数量相关属性
        self.ammo = BULLET_CONFIG["initial_ammo"]  # 当前子弹数量
        self.max_ammo = BULLET_CONFIG["max_ammo"]  # 最大子弹数量
        
        # 状态
        self.is_moving = False
        self.last_direction = "right"
        self.shoot_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0
        self.current_room = 1
        self.just_switched = False
    
    def handle_input(self, keys):
        """处理键盘输入"""
        old_x, old_y = self.x, self.y
        self.is_moving = False
        
        # 移动控制
        if keys[pg.K_w] or keys[pg.K_UP]:
            self.y -= self.speed
            self.direction = 90
            self.is_moving = True
            self.last_direction = "up"
            
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            self.y += self.speed
            self.direction = 270
            self.is_moving = True
            self.last_direction = "down"
            
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.x -= self.speed
            self.direction = 180
            self.is_moving = True
            self.last_direction = "left"
            
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.x += self.speed
            self.direction = 0
            self.is_moving = True
            self.last_direction = "right"
        
        return (old_x, old_y) != (self.x, self.y)
    
    def shoot(self):
        """发射子弹"""
        if (self.shoot_cooldown <= 0 and 
            len(self.bullets) < BULLET_CONFIG["max_bullets"] and 
            self.health_system.is_alive and
            self.ammo > 0):  # 新增条件
            
            bullet = Bullet(
                self.x, self.y, 
                self.direction,
                BULLET_CONFIG["speed"],
                BULLET_CONFIG["damage"],
                BULLET_CONFIG["radius"]
            )
            self.bullets.append(bullet)
            self.shoot_cooldown = BULLET_CONFIG["cooldown"]
            self.ammo -= 1  # 减少子弹数量
            return True
        return False
    
    def update(self, keys, screen_width, screen_height):
        """更新玩家状态"""
        # 处理输入
        self.handle_input(keys)
        
        # 边界检测（确保玩家不会移出屏幕）
        self.x = max(self.radius, min(self.x, screen_width - self.radius))
        self.y = max(self.radius, min(self.y, screen_height - self.radius))
        
        # 更新冷却和无敌时间
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # 更新子弹
        self.update_bullets(screen_width, screen_height)
    
    def update_bullets(self, screen_width, screen_height):
        """更新所有子弹"""
        active_bullets = []
        for bullet in self.bullets:
            bullet.update(screen_width, screen_height)
            if bullet.active:
                active_bullets.append(bullet)
        self.bullets = active_bullets
    
    def take_damage(self, damage):
        """受到伤害"""
        if not self.invincible and self.health_system.is_alive:
            self.health_system.take_damage(damage)
            self.invincible = True
            self.invincible_timer = PLAYER_CONFIG["invincible_duration"]
            return True
        return False
    
    def heal(self, amount):
        """治疗"""
        return self.health_system.heal(amount)
    
    def draw(self, screen):
        """绘制玩家"""
        # 无敌状态闪烁效果
        if self.invincible and self.invincible_timer % 10 < 5:
            # 闪烁时用红色显示
            pg.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)
        else:
            pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
    
    def draw_bullets(self, screen):
        """绘制所有子弹"""
        for bullet in self.bullets:
            bullet.draw(screen)
    
    def draw_health_bar(self, screen, x, y, width=100, height=10):
        """绘制生命值条"""
        # 背景（红色）
        pg.draw.rect(screen, (255, 0, 0), (x, y, width, height))
        
        # 当前生命值（绿色）
        health_width = int(width * self.health_system.get_health_percentage())
        pg.draw.rect(screen, (0, 255, 0), (x, y, health_width, height))
        
        # 边框
        pg.draw.rect(screen, (255, 255, 255), (x, y, width, height), 1)

        # 绘制子弹数量
        ammo_text = f"子弹: {self.ammo}/{self.max_ammo}"
        ammo_surf = pg.font.SysFont("SimHei", 16).render(ammo_text, True, (255, 255, 255))
        screen.blit(ammo_surf, (x, y + 20))  # 绘制在生命值条下方
    
    def get_rect(self):
        """获取碰撞矩形（用于与现有代码兼容）"""
        return pg.Rect(
            self.x - self.radius, 
            self.y - self.radius, 
            self.radius * 2, 
            self.radius * 2
        )
    
    def get_state(self):
        """获取玩家状态（用于与其他模块通信）"""
        return {
            'pos': [self.x, self.y],
            'radius': self.radius,
            'speed': self.speed,
            'current_room': self.current_room,
            'just_switched': self.just_switched,
            'health': self.health_system.current_health,
            'max_health': self.health_system.max_health,
            'alive': self.health_system.is_alive,
            'bullets_count': len(self.bullets),
            'ammo': self.ammo,  
            'max_ammo': self.max_ammo  
        }