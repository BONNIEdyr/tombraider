import pygame as pg
from typing import Dict, List

class Minimap:
    def __init__(self, config: Dict):
        self.config = config
        self.colors = config["ui"]["colors"]
        self.size = 200  # 小地图尺寸
        self.position = (config["screen_width"] - self.size - 20, 20)  # 右上角
        self.room_size = 15  # 地图上每个房间的大小
        self.is_dragging = False
        self.drag_offset = (0, 0)

    def handle_events(self, event: pg.event.Event) -> None:
        """处理小地图拖拽事件"""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            # 检查是否点击小地图区域
            map_rect = pg.Rect(self.position[0], self.position[1], self.size, self.size)
            if map_rect.collidepoint(event.pos):
                self.is_dragging = True
                self.drag_offset = (
                    self.position[0] - event.pos[0],
                    self.position[1] - event.pos[1]
                )
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pg.MOUSEMOTION and self.is_dragging:
            # 更新拖拽位置
            self.position = (
                event.pos[0] + self.drag_offset[0],
                event.pos[1] + self.drag_offset[1]
            )

    def draw(self, screen: pg.Surface, explored_rooms: List[int], current_room: int, 
             room_positions: Dict[int, tuple]) -> None:
        """绘制小地图：已探索房间、当前房间、房间连接"""
        # 绘制地图背景
        map_rect = pg.Rect(self.position[0], self.position[1], self.size, self.size)
        pg.draw.rect(screen, self.colors["LIGHT_GRAY"], map_rect)
        pg.draw.rect(screen, self.colors["BLACK"], map_rect, 2)
        
        # 绘制房间
        for room_id in explored_rooms:
            if room_id in room_positions:
                x, y = room_positions[room_id]
                # 转换为小地图上的坐标
                map_x = self.position[0] + 50 + x * self.room_size
                map_y = self.position[1] + 50 + y * self.room_size
                # 当前房间用红色，其他用棕色
                color = self.colors["RED"] if room_id == current_room else self.colors["BROWN"]
                pg.draw.rect(screen, color, (map_x, map_y, self.room_size, self.room_size))
        
        # 绘制地图标题
        title = pg.font.Font(None, 20).render("地图", True, self.colors["BLACK"])
        screen.blit(title, (self.position[0] + 10, self.position[1] - 20))