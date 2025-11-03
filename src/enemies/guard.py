from .base_enemy import Enemy
import pygame as pg
import numpy as np

SCALE_FACTOR = 0.4

class Guard(Enemy):
    """
    宝藏守卫敌人类。
    功能：在宝藏点附近保持静止或巡逻，一旦玩家进入警戒范围，则移动到宝藏与玩家之间进行阻挡。
    """
    TREASURE_X = 150
    TREASURE_Y = 150
    ALERT_RADIUS = 300
    
    def __init__(self, x, y):
        original_image = pg.image.load("assets/enemies/guard.png").convert_alpha() # 假设存在 knight.png
        
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        guard_image = pg.transform.scale(original_image, (new_w, new_h))
        
        super().__init__(x, y, hp=150, speed=1.5, image=guard_image)
        
        self.is_alert = False

    def update(self, player):
        """守卫的特定逻辑：守卫宝藏区域"""
        
        player_pos = np.array([player.rect.centerx, player.rect.centery])
        guard_pos = np.array([self.rect.centerx, self.rect.centery])
        treasure_pos = np.array([self.TREASURE_X, self.TREASURE_Y])

        distance_to_player = np.linalg.norm(player_pos - guard_pos)
        
        if distance_to_player < self.ALERT_RADIUS:
            self.is_alert = True
        elif distance_to_player > self.ALERT_RADIUS + 50: # 加上一点容错，避免频繁切换
            self.is_alert = False

        if self.is_alert:
            player_to_treasure_vec = treasure_pos - player_pos

            dist_p_t = np.linalg.norm(player_to_treasure_vec)
            if dist_p_t > 0:
                normalized_vec = player_to_treasure_vec / dist_p_t
                block_point = (player_pos + treasure_pos) / 2
                
                target_x, target_y = block_point
            else:
                target_x, target_y = guard_pos

            if target_x < self.rect.centerx:
                self.rect.x -= self.speed
            elif target_x > self.rect.centerx:
                self.rect.x += self.speed

            if target_y < self.rect.centery:
                self.rect.y -= self.speed
            elif target_y > self.rect.centery:
                self.rect.y += self.speed
                
        else:
            pass