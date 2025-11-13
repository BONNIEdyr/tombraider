from .base_enemy import Enemy
import pygame as pg
import numpy as np

SCALE_FACTOR = 0.4

class Guard(Enemy):
    # Enemy that guards a treasure area and blocks the player when in alert range.
    TREASURE_X = 150
    TREASURE_Y = 150
    ALERT_RADIUS = 300
    
    def __init__(self, x, y):
        # Initialize the guard with scaled image and attributes.
        original_image = pg.image.load("assets/enemies/guard.png").convert_alpha()
        original_w, original_h = original_image.get_size()
        new_w = int(original_w * SCALE_FACTOR)
        new_h = int(original_h * SCALE_FACTOR)
        guard_image = pg.transform.scale(original_image, (new_w, new_h))
        
        super().__init__(x, y, hp=150, speed=1.5, image=guard_image)
        self.is_alert = False

    def update(self, player):
        # Update the guard's behavior: guard the treasure area and block the player when nearby.
        player_pos = np.array([player.rect.centerx, player.rect.centery])
        guard_pos = np.array([self.rect.centerx, self.rect.centery])
        treasure_pos = np.array([self.TREASURE_X, self.TREASURE_Y])

        distance_to_player = np.linalg.norm(player_pos - guard_pos)
        
        if distance_to_player < self.ALERT_RADIUS:
            self.is_alert = True
        elif distance_to_player > self.ALERT_RADIUS + 50:
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
