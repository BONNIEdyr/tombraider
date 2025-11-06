# [file name]: src/items/base_item.py
# [file content begin]
import pygame as pg
import random
from abc import ABC, abstractmethod

class Item(ABC):
    """物品基类"""
    def __init__(self, name, rarity, image_path=None):
        self.name = name
        self.rarity = rarity
        self.collected = False
        self.position = [0, 0]
        
        # 根据物品类型设置默认颜色（备用）
        self.default_colors = {
            "Medkit": (255, 0, 0),      # 红色 - 急救包
            "Food": (0, 255, 0),        # 绿色 - 食物
            "Gun": (100, 100, 100),     # 灰色 - 枪支
            "Ammo": (255, 255, 0),      # 黄色 - 弹药
            "Extended Magazine": (0, 0, 255),  # 蓝色 - 弹匣
            "Enhanced Bullets": (255, 0, 255), # 紫色 - 强化子弹
            "Falling Rocks Trap": (128, 128, 128) # 灰色 - 陷阱
        }
        
        # 改进的图片加载方法
        self.image = self.load_image_with_transparency(image_path)
    
    def load_image_with_transparency(self, image_path):
        """改进的图片加载方法，处理透明背景"""
        if not image_path:
            return None
            
        try:
            # 方法1：直接加载为带alpha通道的图片
            image = pg.image.load(image_path)
            
            # 转换为支持透明度的格式
            image = image.convert_alpha()
            
            # 缩放图片
            image = pg.transform.scale(image, (30, 30))
            
            return image
            
        except Exception as e:
            # 如果图片加载失败，返回None使用颜色代替
            return None
    
    def set_position(self, x, y):
        """设置物品位置"""
        self.position = [x, y]
    
    def get_rect(self):
        """获取碰撞矩形"""
        return pg.Rect(self.position[0] - 15, self.position[1] - 15, 30, 30)
    
    def draw(self, screen):
        """绘制物品"""
        if self.image:
            # 绘制图片（已经处理过透明背景）
            screen.blit(self.image, (self.position[0] - 15, self.position[1] - 15))
        else:
            # 备用绘制：使用颜色
            color = self.default_colors.get(self.name, (255, 255, 255))
            pg.draw.circle(screen, color, self.position, 15)
            
            # 根据稀有度绘制边框
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
        """应用物品效果（子类必须实现）"""
        pass
    
    def collect(self, player):
        """收集物品"""
        if not self.collected:
            result = self.apply_effect(player)
            self.collected = True
            return result
        return None
# [file content end]