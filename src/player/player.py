import pygame as pg
import math
from .health_system import HealthSystem
from .bullet import Bullet
from .constants import PLAYER_CONFIG, BULLET_CONFIG, CONTROLS
from src.audio import play_sound

class Player:
    def __init__(self, x, y):
        """Initialize the player with position, health, weapons and other attributes"""
        self.x = x
        self.y = y
        self.radius = PLAYER_CONFIG["radius"]
        self.speed = PLAYER_CONFIG["speed"]
        self.color = PLAYER_CONFIG["color"]
        self.direction = 0
        self.bullet_damage = BULLET_CONFIG["damage"]
        self.has_gun = True
        self.health_system = HealthSystem(PLAYER_CONFIG["max_health"])
        self.bullets = []
        self.ammo = BULLET_CONFIG["initial_ammo"]
        self.max_ammo = BULLET_CONFIG["max_ammo"]
        self.room_bullets = {}
        self.is_moving = False
        self.last_direction = "right"
        self.shoot_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0
        self.current_room = 1
        self.just_switched = False
        try:
            raw = pg.image.load("assets/raider.png").convert_alpha()
            self._raider_image_raw = raw
            w = int(self.radius * 2 * 2.5)
            h = int(self.radius * 2 * 2.5)
            self._raider_image = pg.transform.scale(raw, (w, h))
        except Exception:
            self._raider_image_raw = None
            self._raider_image = None
        try:
            hurt = pg.image.load("assets/hurted.png").convert_alpha()
            w = int(self.radius * 2 * 2.5)
            h = int(self.radius * 2 * 2.5)
            self._hurted_image = pg.transform.scale(hurt, (w, h))
        except Exception:
            self._hurted_image = None
    
    def switch_room(self, new_room_id):
        """Switch to a new room and manage bullets between rooms"""
        self.room_bullets[self.current_room] = []
        self.current_room = new_room_id
        self.just_switched = True
        self.bullets = self.room_bullets.get(new_room_id, [])
    
    def handle_input(self, keys):
        """Process keyboard input for player movement and direction"""
        old_x, old_y = self.x, self.y
        self.is_moving = False
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
        """Fire a bullet if conditions are met"""
        if (self.shoot_cooldown <= 0 and 
            len(self.bullets) < BULLET_CONFIG["max_bullets"] and 
            self.health_system.is_alive and
            self.ammo > 0 and
            self.has_gun
            ):
            bullet = Bullet(
                self.x, self.y, 
                self.direction,
                BULLET_CONFIG["speed"],
                self.bullet_damage,
                BULLET_CONFIG["radius"]
            )
            self.bullets.append(bullet)
            self.shoot_cooldown = BULLET_CONFIG["cooldown"]
            self.ammo -= 1
            try:
                play_sound('bulletshot')
            except Exception:
                pass
            return True
        return False
    
    def update(self, keys, screen_width, screen_height):
        """Update player position, state and bullets"""
        self.handle_input(keys)
        self.x = max(self.radius, min(self.x, screen_width - self.radius))
        self.y = max(self.radius, min(self.y, screen_height - self.radius))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        self.update_bullets(screen_width, screen_height)
    
    def update_bullets(self, screen_width, screen_height):
        """Update all bullets in the current room"""
        active_bullets = []
        for bullet in self.bullets:
            bullet.update(screen_width, screen_height)
            if bullet.active:
                active_bullets.append(bullet)
        self.bullets = active_bullets
    
    def take_damage(self, damage):
        """Apply damage to the player with invincibility frames"""
        if not self.invincible and self.health_system.is_alive:
            self.health_system.take_damage(damage)
            self.invincible = True
            self.invincible_timer = PLAYER_CONFIG["invincible_duration"]
            try:
                play_sound('ough')
            except Exception:
                pass
            return True
        return False
    
    def heal(self, amount):
        """Heal the player by specified amount"""
        return self.health_system.heal(amount)
    
    def draw(self, screen):
        """Draw the player with appropriate sprite based on state"""
        if self.invincible and self.invincible_timer % 10 < 5:
            if getattr(self, '_hurted_image', None) is not None:
                rect = self._hurted_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self._hurted_image, rect.topleft)
            else:
                pg.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)
        else:
            if getattr(self, '_raider_image', None):
                rect = self._raider_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self._raider_image, rect.topleft)
            else:
                pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
    
    def draw_bullets(self, screen):
        """Draw all bullets in the current room"""
        for bullet in self.bullets:
            bullet.draw(screen)
    
    def get_rect(self):
        """Get collision rectangle for the player"""
        return pg.Rect(
            self.x - self.radius, 
            self.y - self.radius, 
            self.radius * 2, 
            self.radius * 2
        )
    
    def get_state(self):
        """Get current player state for external communication"""
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
        """Clear all bullets from all rooms"""
        self.bullets = []
        self.room_bullets.clear()