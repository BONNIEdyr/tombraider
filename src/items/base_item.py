import pygame as pg
import random
from abc import ABC, abstractmethod

class Item(ABC):
    def __init__(self, name, rarity, image_path=None):
        self.name = name
        self.rarity = rarity
        self.collected = False
        self.position = [0, 0]
        
        self.default_colors = {
            "Medkit": (255, 0, 0),
            "Food": (0, 255, 0),
            "Gun": (100, 100, 100),
            "Ammo": (255, 255, 0),
            "Extended Magazine": (0, 0, 255),
            "Enhanced Bullets": (255, 0, 255),
            "Falling Rocks Trap": (128, 128, 128)
        }
        
        self.image = self.load_image_with_transparency(image_path)
    
    def load_image_with_transparency(self, image_path):
        """Load image with transparency handling"""
        if not image_path:
            return None
            
        try:
            image = pg.image.load(image_path)
            image = image.convert_alpha()
            image = pg.transform.scale(image, (30, 30))
            return image
            
        except Exception as e:
            return None
    
    def set_position(self, x, y):
        """Set item position"""
        self.position = [x, y]
    
    def get_rect(self):
        """Get collision rectangle"""
        return pg.Rect(self.position[0] - 15, self.position[1] - 15, 30, 30)
    
    def draw(self, screen):
        """Draw the item on screen"""
        if self.image:
            screen.blit(self.image, (self.position[0] - 15, self.position[1] - 15))
        else:
            color = self.default_colors.get(self.name, (255, 255, 255))
            pg.draw.circle(screen, color, self.position, 15)
            
            border_colors = {
                "common": (200, 200, 200),
                "uncommon": (0, 255, 0),
                "rare": (0, 0, 255),
                "epic": (255, 0, 255)
            }
            border_color = border_colors.get(self.rarity, (255, 255, 255))
            pg.draw.circle(screen, border_color, self.position, 15, 2)
    
    @abstractmethod
    def apply_effect(self, player):
        """Apply item effect to player"""
        pass
    
    def collect(self, player):
        """Collect the item and apply its effect"""
        if not self.collected:
            result = self.apply_effect(player)
            self.collected = True
            return result
        return None
