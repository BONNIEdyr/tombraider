import pygame

class Enemy(pygame.sprite.Sprite):
    # This class defines a base enemy with health, speed, and position.
    def __init__(self, x, y, hp, speed, image):
        # Initialize the enemy with position, health, and speed.
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = hp
        self.max_hp = hp
        self.speed = speed

    # This function defines general enemy logic, such as moving toward the player.
    def update(self, player):
        pass

    # This function applies damage to the enemy and kills it if HP reaches zero.
    def take_damage(self, amount: int) -> None:
        try:
            self.hp -= amount
        except Exception:
            self.hp = 0

        if self.hp <= 0:
            try:
                if hasattr(self, 'on_death'):
                    self.on_death()
            except Exception:
                pass
            self.kill()

    # This function draws the enemy's health bar above its sprite.
    def draw_health_bar(self, surface: pygame.Surface) -> None:
        if not hasattr(self, 'hp') or not hasattr(self, 'max_hp'):
            return

        bar_width = max(24, self.rect.width)
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - bar_height - 4

        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (60, 60, 60), bg_rect)

        hp_ratio = max(0.0, min(1.0, float(self.hp) / float(self.max_hp) if self.max_hp else 0.0))
        fg_rect = pygame.Rect(bar_x, bar_y, int(bar_width * hp_ratio), bar_height)
        pygame.draw.rect(surface, (0, 200, 0), fg_rect)

        pygame.draw.rect(surface, (0, 0, 0), bg_rect, 1)
