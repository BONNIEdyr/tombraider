import pygame


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, hp, speed, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = hp
        # store max_hp for drawing health bar
        self.max_hp = hp
        self.speed = speed

    def update(self, player):
        """所有敌人共有的逻辑写这里（比如朝玩家移动）"""
        pass

    def take_damage(self, amount: int) -> None:
        """Apply damage to this enemy. Kill the sprite when hp <= 0."""
        try:
            self.hp -= amount
        except Exception:
            # ensure hp is numeric
            self.hp = 0

        if self.hp <= 0:
            # allow subclasses to react (drop loot, play animation) before killing
            try:
                if hasattr(self, 'on_death'):
                    self.on_death()
            except Exception:
                pass
            self.kill()

    def draw_health_bar(self, surface: pygame.Surface) -> None:
        """Draw a simple health bar above the enemy.

        Bar dimensions are proportional to the enemy width.
        """
        if not hasattr(self, 'hp') or not hasattr(self, 'max_hp'):
            return

        bar_width = max(24, self.rect.width)
        bar_height = 5
        # position the bar slightly above the enemy
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - bar_height - 4

        # background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (60, 60, 60), bg_rect)

        # foreground based on hp ratio
        hp_ratio = max(0.0, min(1.0, float(self.hp) / float(self.max_hp) if self.max_hp else 0.0))
        fg_rect = pygame.Rect(bar_x, bar_y, int(bar_width * hp_ratio), bar_height)
        pygame.draw.rect(surface, (0, 200, 0), fg_rect)

        # border
        pygame.draw.rect(surface, (0, 0, 0), bg_rect, 1)
