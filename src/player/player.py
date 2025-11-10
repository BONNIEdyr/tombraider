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
         # 新增：武器系统属性
        self.bullet_damage = BULLET_CONFIG["damage"]  # 基础伤害
        self.has_gun = True  # 默认有枪

        
        # 系统组件
        self.health_system = HealthSystem(PLAYER_CONFIG["max_health"])
        self.bullets = []  # 当前房间的子弹

        # 子弹数量相关属性
        self.ammo = BULLET_CONFIG["initial_ammo"]  # 当前子弹数量
        self.max_ammo = BULLET_CONFIG["max_ammo"]  # 最大子弹数量
        
        # 房间子弹管理
        self.room_bullets = {}  # room_id -> bullets list
        
        # 状态
        self.is_moving = False
        self.last_direction = "right"
        self.shoot_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0
        self.current_room = 1
        self.just_switched = False
        # 尝试加载玩家图片（可选），若不存在则保留为 None
        try:
            raw = pg.image.load("assets/raider.png").convert_alpha()
            self._raider_image_raw = raw
            # 原先放大 5 倍，现在改为放大至原来的 2.5 倍（即之前的一半）
            w = int(self.radius * 2 * 2.5)
            h = int(self.radius * 2 * 2.5)
            self._raider_image = pg.transform.scale(raw, (w, h))
        except Exception:
            self._raider_image_raw = None
            self._raider_image = None
        # 加载受伤显示图片（hurted.png），用于替换红色圆球效果
        try:
            hurt = pg.image.load("assets/hurted.png").convert_alpha()
            w = int(self.radius * 2 * 2.5)
            h = int(self.radius * 2 * 2.5)
            self._hurted_image = pg.transform.scale(hurt, (w, h))
        except Exception:
            self._hurted_image = None
    
    def switch_room(self, new_room_id):
        """切换房间时清除当前房间子弹"""
        # 不保存子弹，直接清除当前房间的子弹
        self.room_bullets[self.current_room] = []
        
        # 切换到新房间
        self.current_room = new_room_id
        self.just_switched = True
        
        # 加载新房间的子弹（如果有）
        self.bullets = self.room_bullets.get(new_room_id, [])
    
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
            self.ammo > 0 and
            self.has_gun
            ):  # 新增条件
            
            bullet = Bullet(
                self.x, self.y, 
                self.direction,
                BULLET_CONFIG["speed"],
                self.bullet_damage,
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
        """更新当前房间的子弹"""
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
            # 闪烁时使用 hurted 图片（若存在），否则红色圆球
            if getattr(self, '_hurted_image', None) is not None:
                rect = self._hurted_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self._hurted_image, rect.topleft)
            else:
                pg.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)
        else:
            # 优先使用外部图片（assets/raider.png），没有图片时回退到圆形
            if getattr(self, '_raider_image', None):
                rect = self._raider_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self._raider_image, rect.topleft)
            else:
                pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
    
    def draw_bullets(self, screen):
        """绘制当前房间的子弹"""
        for bullet in self.bullets:
            bullet.draw(screen)
    
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
    
    def clear_all_bullets(self):
        """清空所有房间的子弹（用于重启游戏）"""
        self.bullets = []
        self.room_bullets.clear()