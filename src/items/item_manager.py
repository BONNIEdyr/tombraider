# [file name]: src/items/item_manager.py
# [file content begin]
import pygame as pg
import random
import json
import os
import sys
import copy
from abc import ABC, abstractmethod
from src.audio import play_sound

# 基础物品类（保持不变）
class Item(ABC):
    """物品基类"""
    def __init__(self, name, rarity, image_path=None):
        self.name = name
        self.rarity = rarity
        self.collected = False
        self.position = [0, 0]
        
        self.default_colors = {
            "Medkit": (255, 0, 0),
            "Food": (0, 255, 0),
            #"Gun": (100, 100, 100),
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

# 具体物品类（保持不变）
class Medkit(Item):
    def __init__(self):
        super().__init__("Medkit", "rare", "assets/items/medkit.png")
    
    def apply_effect(self, player):
        heal_amount = int(player.health_system.max_health * 0.5)
        player.heal(heal_amount)
        try:
            play_sound('HP_up')
        except Exception:
            pass
        return f"Picked up Medkit! Restored {heal_amount} HP."

class Food(Item):
    def __init__(self):
        super().__init__("Food", "uncommon", "assets/items/food.png")
    
    def apply_effect(self, player):
        heal_amount = int(player.health_system.max_health * 0.2)
        player.heal(heal_amount)
        try:
            play_sound('HP_up')
        except Exception:
            pass
        return f"Ate Food! Restored {heal_amount} HP."
class Gun(Item):
    def __init__(self):
        super().__init__("Gun", "uncommon", "assets/items/gun.png")
        self.ammo_amount = 15
    
    def apply_effect(self, player):
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"Picked up Gun! +{self.ammo_amount} ammo."

class Ammo(Item):
    def __init__(self):
        super().__init__("Ammo", "common", "assets/items/ammo.png")
        self.ammo_amount = 10
    
    def apply_effect(self, player):
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"Picked up Ammo! +{self.ammo_amount} ammo."

class ExtendedMagazine(Item):
    def __init__(self):
        super().__init__("Extended Magazine", "rare", "assets/items/magazine.png")
        self.capacity_increase = 10
    
    def apply_effect(self, player):
        player.max_ammo += self.capacity_increase
        return f"Extended Magazine! Max ammo +{self.capacity_increase}."


class EnhancedBullets(Item):
    def __init__(self):
        super().__init__("Enhanced Bullets", "epic", "assets/items/bullets.png")
        self.damage_increase = 5
    
    def apply_effect(self, player):
        if hasattr(player, 'bullet_damage'):
            player.bullet_damage += self.damage_increase
        return f"Enhanced Bullets! Damage +{self.damage_increase}."

class FallingRocksTrap(Item):
    def __init__(self):
        super().__init__("Falling Rocks Trap", "common", "assets/items/rocks_trap.png")
        self.activated = False
        self.activation_timer = 0
    
    def apply_effect(self, player):
        if not self.activated:
            damage = int(player.health_system.max_health * 0.4)
            player.take_damage(damage)
            self.activated = True
            self.activation_timer = 60
            try:
                play_sound('ough')
            except Exception:
                pass
            return f"Hit by falling rocks! Took {damage} damage!"
        return ""
    
    def draw(self, screen):
        if self.activated and self.activation_timer > 0:
            pg.draw.circle(screen, (255, 0, 0), self.position, 15)
            self.activation_timer -= 1
        else:
            super().draw(screen)
    
    def update(self):
        if self.activated and self.activation_timer > 0:
            self.activation_timer -= 1

# 改进的物品管理器类 - 移除调试输出
class ItemManager:
    """管理游戏中的所有物品和陷阱"""
    
    def __init__(self, rooms_config, auto_load=True):
        self.rooms_config = rooms_config
        self.room_items = {}  # room_id -> list of items
        self.initialize_items()

    def is_valid_position(self, x, y, room_data):
        """基于实际墙壁数据的精确位置检测"""
        # 创建物品矩形
        item_rect = pg.Rect(x - 15, y - 15, 30, 30)
        
        # 检查与所有墙壁的碰撞
        for wall in room_data["walls"]:
            wall_rect = pg.Rect(wall[0], wall[1], wall[2], wall[3])
            if item_rect.colliderect(wall_rect):
                return False
        
        # 检查特殊区域
        room_id = room_data["room_id"]
        
        # 出口区域（房间20）
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
        
        # 入口区域（房间1）
        if room_id == 1:
            entrance_rect = pg.Rect(0, 250, 50, 100)
            if item_rect.colliderect(entrance_rect):
                return False
        
        # 确保不在边界上
        if x < 40 or x > 760 or y < 40 or y > 560:
            return False
            
        return True
    
    def get_room_safe_zones(self, room_data):
        """为每个房间生成安全区域"""
        safe_zones = []
        room_id = room_data["room_id"]
        
        # 为每个房间预定义安全区域（基于实际墙壁布局）
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
        
        # 如果有预定义的安全区域，使用它们
        if room_id in room_safe_areas:
            for pos in room_safe_areas[room_id]:
                if self.is_valid_position(pos[0], pos[1], room_data):
                    safe_zones.append(pos)
        
        # 如果没有预定义区域或需要更多位置，生成随机位置
        if len(safe_zones) < 8:
            for _ in range(20):
                x = random.randint(60, 740)
                y = random.randint(60, 540)
                if self.is_valid_position(x, y, room_data):
                    # 检查与已有位置的距离
                    too_close = False
                    for existing_pos in safe_zones:
                        if (abs(existing_pos[0] - x) < 50 and 
                            abs(existing_pos[1] - y) < 50):
                            too_close = True
                            break
                    if not too_close:
                        safe_zones.append((x, y))
                        if len(safe_zones) >= 12:  # 最多12个安全位置
                            break
        
        return safe_zones
    
    def analyze_room_layout(self, room_data):
        """分析房间布局，找到开放区域"""
        walls = room_data["walls"]
        
        # 找到房间中的开放区域中心点
        open_areas = []
        
        # 检查几个关键区域是否开放
        test_points = [
            (200, 150), (400, 150), (600, 150),
            (200, 300), (400, 300), (600, 300), 
            (200, 450), (400, 450), (600, 450)
        ]
        
        for point in test_points:
            if self.is_valid_position(point[0], point[1], room_data):
                # 检查周围区域是否也开放
                open_count = 0
                for dx in [-40, 0, 40]:
                    for dy in [-40, 0, 40]:
                        if self.is_valid_position(point[0] + dx, point[1] + dy, room_data):
                            open_count += 1
                
                # 如果周围大部分区域开放，则认为是好的位置
                if open_count >= 5:
                    open_areas.append(point)
        
        return open_areas
    
    def initialize_items(self):
        """根据配置初始化所有房间的物品"""
        
        # 物品类型和它们的生成权重
        item_weights = {
            "food": 30,           # 食物 - 最常见
            "ammo": 25,           # 弹药 - 常见
            "trap": 20,           # 陷阱 - 较常见
            "medkit": 10,         # 急救包 - 稀有
            "gun": 0,             # 枪支 - 稀有
            "magazine": 4,        # 扩容弹匣 - 很稀有
            "enhanced_bullets": 3 # 强化弹头 - 最稀有
        }
        
        # 为每个房间生成物品
        for room in self.rooms_config["rooms"]:
            room_id = room["room_id"]
            self.room_items[room_id] = []
            
            # 根据房间ID决定物品数量
            if room_id in [1, 20]:  # 入口和出口房间
                num_items = random.randint(1, 2)
            elif room_id in [5, 10, 15]:  # 关键房间
                num_items = random.randint(2, 4)
            else:  # 普通房间
                num_items = random.randint(1, 3)
            
            # 获取安全位置
            safe_zones = self.get_room_safe_zones(room)
            open_areas = self.analyze_room_layout(room)
            
            # 合并安全位置
            all_safe_positions = list(set(safe_zones + open_areas))
            
            if not all_safe_positions:
                # 如果实在找不到安全位置，跳过这个房间
                continue
            
            # 随机打乱位置
            random.shuffle(all_safe_positions)
            
            items_placed = 0
            for i in range(min(num_items, len(all_safe_positions))):
                # 随机选择物品类型
                item_type = random.choices(
                    list(item_weights.keys()), 
                    weights=list(item_weights.values())
                )[0]
                
                # 创建物品实例
                item = self.create_item(item_type)
                if item:
                    # 使用安全位置
                    x, y = all_safe_positions[i]
                    item.set_position(x, y)
                    self.room_items[room_id].append(item)
                    items_placed += 1
    
    def create_item(self, item_type):
        """根据类型创建物品实例"""
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
        """获取指定房间的物品列表"""
        return self.room_items.get(room_id, [])
    
    def check_collisions(self, player, current_room_id):
        """检查玩家与物品的碰撞"""
        player_rect = player.get_rect()
        collected_items = []
        message = None
        
        for item in self.room_items.get(current_room_id, []):
            if not item.collected and player_rect.colliderect(item.get_rect()):
                result = item.collect(player)
                if result:  # 如果有返回消息
                    # 确保消息是字符串
                    if not isinstance(result, str):
                        result = str(result)
                    message = result
                    collected_items.append(item)
        
        # 移除已收集的物品
        for item in collected_items:
            if item in self.room_items[current_room_id]:
                self.room_items[current_room_id].remove(item)
            
        return message
    
    def draw_room_items(self, screen, current_room_id):
        """绘制当前房间的所有物品"""
        for item in self.room_items.get(current_room_id, []):
            item.draw(screen)
    
    def update_traps(self):
        """更新所有陷阱的状态"""
        for room_items in self.room_items.values():
            for item in room_items:
                if hasattr(item, 'update'):
                    item.update()
    
    def save_state(self):
        """保存物品状态到文件"""
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
            print("[DEBUG] 物品状态加载完成（旧存档已恢复）。")
        except:
            print("[DEBUG] 加载失败，初始化新物品。")
            self.initialize_items()

    
    def get_type_key(self, class_name):
        """将类名映射回类型键"""
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
    
# [file content end]