import pygame as pg
from typing import Dict, List, Tuple, Any

class Minimap:
    def __init__(self, config: Dict):
        self.config = config
        self.colors = config["ui"]["colors"]

        minimap_config = config["minimap"]
        self.w = minimap_config["width"]
        self.h = minimap_config["height"]
        self.x = minimap_config["x"]
        self.y = minimap_config["y"]
        self.cell_size = minimap_config["cell_size"]
        
        self.is_dragging = False
        self.drag_off_x = 0
        self.drag_off_y = 0

    # This function handles minimap dragging events
    def handle_events(self, event: pg.event.Event) -> None:
        if event.type == pg.MOUSEBUTTONDOWN:
            minimap_rect = pg.Rect(self.x, self.y, self.w, self.h)
            if minimap_rect.collidepoint(event.pos):
                self.is_dragging = True
                self.drag_off_x = event.pos[0] - self.x
                self.drag_off_y = event.pos[1] - self.y
        elif event.type == pg.MOUSEBUTTONUP:
            self.is_dragging = False
        elif event.type == pg.MOUSEMOTION and self.is_dragging:
            new_x = event.pos[0] - self.drag_off_x
            new_y = event.pos[1] - self.drag_off_y
            self.x = max(0, min(new_x, self.config["game"]["screen_width"] - self.w))
            self.y = max(0, min(new_y, self.config["game"]["screen_height"] - self.h))

    # This function draws the minimap including explored rooms, current room, and room connections
    def draw(self, screen: pg.Surface, room_minimap_pos: Dict[int, Tuple[int, int]], 
             room_neighbors: Dict[str, Dict[str, int]], player: Any) -> None:
        minimap_rect = pg.Rect(self.x, self.y, self.w, self.h)
        pg.draw.rect(screen, self.colors["GRAY"], minimap_rect)
        pg.draw.rect(screen, self.colors["BLACK"], minimap_rect, 2)

        if not room_minimap_pos:
            return

        all_x = [pos[0] for pos in room_minimap_pos.values()]
        all_y = [pos[1] for pos in room_minimap_pos.values()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        offset_x = self.x + (self.w - (max_x - min_x + self.cell_size)) // 2
        offset_y = self.y + (self.h - (max_y - min_y + self.cell_size)) // 2

        room_rects = {}
        for room_id, (rel_x, rel_y) in room_minimap_pos.items():
            draw_x = offset_x + (rel_x - min_x)
            draw_y = offset_y + (rel_y - min_y)
            room_rect = pg.Rect(draw_x, draw_y, self.cell_size, self.cell_size)
            pg.draw.rect(screen, self.colors["LIGHT_GRAY"], room_rect)
            pg.draw.rect(screen, self.colors["BLACK"], room_rect, 1)
            room_rects[room_id] = room_rect

        for curr_room_id, connections in room_neighbors.items():
            curr_room_id = int(curr_room_id)
            if curr_room_id not in room_rects:
                continue
            for direction, neighbor_id in connections.items():
                if neighbor_id not in room_rects:
                    continue
                curr_rect = room_rects[curr_room_id]
                neighbor_rect = room_rects[neighbor_id]
                if direction == "right":
                    pg.draw.line(screen, self.colors["BLACK"], curr_rect.midright, neighbor_rect.midleft, 2)
                elif direction == "left":
                    pg.draw.line(screen, self.colors["BLACK"], curr_rect.midleft, neighbor_rect.midright, 2)
                elif direction == "top":
                    pg.draw.line(screen, self.colors["BLACK"], curr_rect.midtop, neighbor_rect.midbottom, 2)
                elif direction == "bottom":
                    pg.draw.line(screen, self.colors["BLACK"], curr_rect.midbottom, neighbor_rect.midtop, 2)

        current_room_id = player.current_room if hasattr(player, 'current_room') else player["current_room"]
        if current_room_id in room_rects:
            pg.draw.circle(screen, self.colors["RED"], room_rects[current_room_id].center, 3)