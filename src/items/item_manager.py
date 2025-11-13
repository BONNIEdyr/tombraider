import pygame as pg
import random
import json
import os
import sys
import copy
from abc import ABC, abstractmethod
from src.audio import play_sound

class Item(ABC):
    def __init__(self, name, rarity, image_path=None):
        self.name = name
        self.rarity = rarity
        self.collected = False
        self.position = [0, 0]
        
        self.default_colors = {
            "Medkit": (255, 0, 0),
            "Food": (0, 255, 0),
            "Ammo": (255, 255, 0),
            "Extended Magazine": (0, 0, 255),
            "Enhanced Bullets": (255, 0, 255),
            "Falling Rocks Trap": (128, 128, 128)
        }
        
        self.image = None
        if image_path:
            try:
                self.image = pg.image.load(image_path).convert_alpha()
                self.image = pg.transform.scale(self.image, (30, 30))
            except:
                self.image = None
    
    def set_position(self, x, y):
        self.position = [x, y]
    
    def get_rect(self):
        return pg.Rect(self.position[0] - 15, self.position[1] - 15, 30, 30)
    
    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.position[0] - 15, self.position[1] - 15))
        else:
            color = self.default_colors.get(self.name, (255, 255, 255))
            pg.draw.circle(screen, color, self.position, 15)
    
    @abstractmethod
    def apply_effect(self, player):
        pass
    
    def collect(self, player):
        if not self.collected:
            result = self.apply_effect(player)
            self.collected = True
            return result
        return None

class Medkit(Item):
    def __init__(self):
        super().__init__("Medkit", "rare", "assets/items/medkit.png")
    
    def apply_effect(self, player):
        """Heal the player by 50% of max health"""
        heal_amount = int(player.health_system.max_health * 0.5)
        player.heal(heal_amount)
        try:
            play_sound('HP_up', volume= 0.3)
        except Exception:
            pass
        return f"Picked up Medkit! Restored {heal_amount} HP."

class Food(Item):
    def __init__(self):
        super().__init__("Food", "uncommon", "assets/items/food.png")
    
    def apply_effect(self, player):
        """Heal the player by 20% of max health"""
        heal_amount = int(player.health_system.max_health * 0.2)
        player.heal(heal_amount)
        try:
            play_sound('HP_up', volume=0.3)
        except Exception:
            pass
        return f"Ate Food! Restored {heal_amount} HP."

class Gun(Item):
    def __init__(self):
        super().__init__("Gun", "uncommon", "assets/items/gun.png")
        self.ammo_amount = 15
    
    def apply_effect(self, player):
        """Add ammo to player"""
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"Picked up Gun! +{self.ammo_amount} ammo."

class Ammo(Item):
    def __init__(self):
        super().__init__("Ammo", "common", "assets/items/ammo.png")
        self.ammo_amount = 10
    
    def apply_effect(self, player):
        """Add ammo to player"""
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"Picked up Ammo! +{self.ammo_amount} ammo."

class ExtendedMagazine(Item):
    def __init__(self):
        super().__init__("Extended Magazine", "rare", "assets/items/magazine.png")
        self.capacity_increase = 10
    
    def apply_effect(self, player):
        """Increase player's max ammo capacity"""
        player.max_ammo += self.capacity_increase
        return f"Extended Magazine! Max ammo +{self.capacity_increase}."

class EnhancedBullets(Item):
    def __init__(self):
        super().__init__("Enhanced Bullets", "epic", "assets/items/bullets.png")
        self.damage_increase = 5
    
    def apply_effect(self, player):
        """Increase player's bullet damage"""
        if hasattr(player, 'bullet_damage'):
            player.bullet_damage += self.damage_increase
        return f"Enhanced Bullets! Damage +{self.damage_increase}."

class FallingRocksTrap(Item):
    def __init__(self):
        super().__init__("Falling Rocks Trap", "common", "assets/items/rocks_trap.png")
        self.activated = False
        self.activation_timer = 0
    
    def apply_effect(self, player):
        """Damage player when trap is activated"""
        if not self.activated:
            damage = int(player.health_system.max_health * 0.4)
            player.take_damage(damage)
            self.activated = True
            self.activation_timer = 60
            try:
                play_sound('ough', volume=0.7)
            except Exception:
                pass
            return f"Hit by falling rocks! Took {damage} damage!"
        return ""
    
    def draw(self, screen):
        """Draw trap with red color when activated"""
        if self.activated and self.activation_timer > 0:
            pg.draw.circle(screen, (255, 0, 0), self.position, 15)
            self.activation_timer -= 1
        else:
            super().draw(screen)
    
    def update(self):
        """Update trap activation timer"""
        if self.activated and self.activation_timer > 0:
            self.activation_timer -= 1

class ItemManager:
    def __init__(self, rooms_config, auto_load=True):
        self.rooms_config = rooms_config
        self.room_items = {}
        self.initialize_items()

    def is_valid_position(self, x, y, room_data):
        """Check if position is valid (not colliding with walls or special areas)"""
        item_rect = pg.Rect(x - 15, y - 15, 30, 30)
        
        for wall in room_data["walls"]:
            wall_rect = pg.Rect(wall[0], wall[1], wall[2], wall[3])
            if item_rect.colliderect(wall_rect):
                return False
        
        room_id = room_data["room_id"]
        
        if room_id == 20:
            exit_area = self.rooms_config["exit_detection"]
            exit_rect = pg.Rect(
                exit_area["x_min"],
                exit_area["y_min"],
                800 - exit_area["x_min"],
                exit_area["y_max"] - exit_area["y_min"]
            )
            if item_rect.colliderect(exit_rect):
                return False
        
        if room_id == 1:
            entrance_rect = pg.Rect(0, 250, 50, 100)
            if item_rect.colliderect(entrance_rect):
                return False
        
        if x < 40 or x > 760 or y < 40 or y > 560:
            return False
            
        return True
    
    def get_room_safe_zones(self, room_data):
        """Generate safe zones for item placement in a room"""
        safe_zones = []
        room_id = room_data["room_id"]
        
        room_safe_areas = {
            1: [(100, 100), (300, 100), (500, 100), (700, 100), 
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            2: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            3: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            4: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            5: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            6: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            7: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            8: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            9: [(100, 100), (300, 100), (500, 100), (700, 100),
                (100, 300), (300, 300), (500, 300), (700, 300),
                (100, 500), (300, 500), (500, 500), (700, 500)],
            10: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            11: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            12: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            13: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            14: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            15: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            16: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            17: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            18: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            19: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)],
            20: [(100, 100), (300, 100), (500, 100), (700, 100),
                 (100, 300), (300, 300), (500, 300), (700, 300),
                 (100, 500), (300, 500), (500, 500), (700, 500)]
        }
        
        if room_id in room_safe_areas:
            for pos in room_safe_areas[room_id]:
                if self.is_valid_position(pos[0], pos[1], room_data):
                    safe_zones.append(pos)
        
        if len(safe_zones) < 8:
            for _ in range(20):
                x = random.randint(60, 740)
                y = random.randint(60, 540)
                if self.is_valid_position(x, y, room_data):
                    too_close = False
                    for existing_pos in safe_zones:
                        if (abs(existing_pos[0] - x) < 50 and 
                            abs(existing_pos[1] - y) < 50):
                            too_close = True
                            break
                    if not too_close:
                        safe_zones.append((x, y))
                        if len(safe_zones) >= 12:
                            break
        
        return safe_zones
    
    def analyze_room_layout(self, room_data):
        """Analyze room layout to find open areas for item placement"""
        walls = room_data["walls"]
        
        open_areas = []
        
        test_points = [
            (200, 150), (400, 150), (600, 150),
            (200, 300), (400, 300), (600, 300), 
            (200, 450), (400, 450), (600, 450)
        ]
        
        for point in test_points:
            if self.is_valid_position(point[0], point[1], room_data):
                open_count = 0
                for dx in [-40, 0, 40]:
                    for dy in [-40, 0, 40]:
                        if self.is_valid_position(point[0] + dx, point[1] + dy, room_data):
                            open_count += 1
                
                if open_count >= 5:
                    open_areas.append(point)
        
        return open_areas
    
    def initialize_items(self):
        """Initialize items for all rooms based on configuration"""
        item_weights = {
            "food": 30,
            "ammo": 25,
            "trap": 20,
            "medkit": 10,
            "gun": 0,
            "magazine": 4,
            "enhanced_bullets": 3
        }
        
        for room in self.rooms_config["rooms"]:
            room_id = room["room_id"]
            self.room_items[room_id] = []
            
            if room_id in [1, 20]:
                num_items = random.randint(1, 2)
            elif room_id in [5, 10, 15]:
                num_items = random.randint(2, 4)
            else:
                num_items = random.randint(1, 3)
            
            safe_zones = self.get_room_safe_zones(room)
            open_areas = self.analyze_room_layout(room)
            
            all_safe_positions = list(set(safe_zones + open_areas))
            
            if not all_safe_positions:
                continue
            
            random.shuffle(all_safe_positions)
            
            items_placed = 0
            for i in range(min(num_items, len(all_safe_positions))):
                item_type = random.choices(
                    list(item_weights.keys()), 
                    weights=list(item_weights.values())
                )[0]
                
                item = self.create_item(item_type)
                if item:
                    x, y = all_safe_positions[i]
                    item.set_position(x, y)
                    self.room_items[room_id].append(item)
                    items_placed += 1
    
    def create_item(self, item_type):
        """Create item instance based on type"""
        if item_type == "food":
            return Food()
        elif item_type == "medkit":
            return Medkit()
        elif item_type == "gun":
            return Gun()
        elif item_type == "ammo":
            return Ammo()
        elif item_type == "magazine":
            return ExtendedMagazine()
        elif item_type == "enhanced_bullets":
            return EnhancedBullets()
        elif item_type == "trap":
            return FallingRocksTrap()
        return None
    
    def get_room_items(self, room_id):
        """Get list of items in specified room"""
        return self.room_items.get(room_id, [])
    
    def check_collisions(self, player, current_room_id):
        """Check for collisions between player and items"""
        player_rect = player.get_rect()
        collected_items = []
        message = None
        
        for item in self.room_items.get(current_room_id, []):
            if not item.collected and player_rect.colliderect(item.get_rect()):
                result = item.collect(player)
                if result:
                    if not isinstance(result, str):
                        result = str(result)
                    message = result
                    collected_items.append(item)
        
        for item in collected_items:
            if item in self.room_items[current_room_id]:
                self.room_items[current_room_id].remove(item)
            
        return message
    
    def draw_room_items(self, screen, current_room_id):
        """Draw all items in current room"""
        for item in self.room_items.get(current_room_id, []):
            item.draw(screen)
    
    def update_traps(self):
        """Update state of all traps"""
        for room_items in self.room_items.values():
            for item in room_items:
                if hasattr(item, 'update'):
                    item.update()
    
    def save_state(self):
        """Save item states to file"""
        state = {}
        for room_id, items in self.room_items.items():
            state[room_id] = []
            for item in items:
                state[room_id].append({
                    'type': item.__class__.__name__,
                    'position': item.position,
                    'collected': item.collected
                })
        
        try:
            with open('config/items_state.json', 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def load_state(self):
        """Load item states from file"""
        try:
            with open('config/items_state.json', 'r') as f:
                state = json.load(f)
            for room_id, items_data in state.items():
                room_id = int(room_id)
                self.room_items[room_id] = []
                for item_data in items_data:
                    item_type = item_data['type']
                    item = self.create_item(self.get_type_key(item_type))
                    if item:
                        item.position = item_data['position']
                        item.collected = item_data['collected']
                        self.room_items[room_id].append(item)
        except:
            self.initialize_items()

    def get_type_key(self, class_name):
        """Map class name back to type key"""
        mapping = {
            'Food': 'food',
            'Medkit': 'medkit', 
            'Gun': 'gun',
            'Ammo': 'ammo',
            'ExtendedMagazine': 'magazine',
            'EnhancedBullets': 'enhanced_bullets',
            'FallingRocksTrap': 'trap'
        }
        return mapping.get(class_name, 'food')
