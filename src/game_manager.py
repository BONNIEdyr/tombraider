import pygame as pg
import json
import copy
import random
from src.enemies.enemy_manager import EnemyManager
from src.player.player import Player
from src.items.item_manager import ItemManager
from src.gui.minimap import Minimap

class GameManager:
    def __init__(self, config):
        self.config = config
        self.wall_width = config["game"]["wall_width"]
        self.screen_width = config["game"]["screen_width"]
        self.screen_height = config["game"]["screen_height"]
        
        # 初始化游戏状态
        self.player, self.game_state, self.explored_rooms, self.room_minimap_pos = self.init_global_state()
        self.minimap = Minimap(config)
        
        # 加载房间配置
        with open('config/rooms_config.json', 'r', encoding='utf-8') as f:
            self.rooms_config = json.load(f)
        self.rooms_config["rooms"] = [copy.deepcopy(room) for room in self.rooms_config["rooms"]]
        self.room_neighbors = self.rooms_config["room_neighbors"]
        
        # 初始化管理器
        self.enemy_manager = EnemyManager(self.rooms_config)
        self.item_manager = ItemManager(self.rooms_config)
        self.enemy_manager.load_all_rooms()
        self.enemy_manager.activate_room(self.player.current_room)

    def init_global_state(self):
        player = Player(
            self.config["player"]["initial_pos"][0],
            self.config["player"]["initial_pos"][1]
        )
        player.current_room = self.config["player"]["initial_room"]
        player.just_switched = False
        
        game_state = {"has_treasure": False, "tip_text": "", "tip_timer": 0}
        explored_rooms = [self.config["player"]["initial_room"]]
        room_minimap_pos = {self.config["player"]["initial_room"]: (0, 0)}
        return player, game_state, explored_rooms, room_minimap_pos

    def get_player_rect(self):
        if hasattr(self.player, 'get_rect'):
            return self.player.get_rect()
        else:
            return pg.Rect(self.player["pos"][0] - self.player["radius"], 
                          self.player["pos"][1] - self.player["radius"],
                          self.player["radius"] * 2, self.player["radius"] * 2)

    def show_tip(self, text, duration=None):
        if duration is None:
            duration = self.config["game"]["tip_duration"]
        
        if text is None:
            text = ""
        elif not isinstance(text, str):
            text = str(text)

        self.game_state["tip_text"] = text
        self.game_state["tip_timer"] = duration * 60

    def check_wall_collision(self, new_pos):
        current_room_data = self.get_current_room()
        player_rect = pg.Rect(new_pos[0] - self.player.radius, new_pos[1] - self.player.radius,
                              self.player.radius * 2, self.player.radius * 2)

        for wall in current_room_data["walls"]:
            wall_rect = pg.Rect(wall[0], wall[1], wall[2], wall[3])
            in_gap = False

            for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
                if gap_dir in ["left", "right"]:
                    gap_x, gap_y_min, gap_y_max = gap_info
                    if gap_dir == "right" and wall_rect.x == gap_x and gap_y_min <= new_pos[1] <= gap_y_max:
                        in_gap = True
                    elif gap_dir == "left" and (wall_rect.x + wall_rect.width) == gap_x and gap_y_min <= new_pos[1] <= gap_y_max:
                        in_gap = True
                elif gap_dir in ["top", "bottom"]:
                    gap_x_min, gap_x_max, gap_y = gap_info
                    if gap_dir == "top" and (wall_rect.y + wall_rect.height) == gap_y and gap_x_min <= new_pos[0] <= gap_x_max:
                        in_gap = True
                    elif gap_dir == "bottom" and wall_rect.y == gap_y and gap_x_min <= new_pos[0] <= gap_x_max:
                        in_gap = True
                if in_gap:
                    break

            if not in_gap and player_rect.colliderect(wall_rect):
                return True
        return False

    def handle_input(self):
        keys = pg.key.get_pressed()
        self.player.update(keys, self.screen_width, self.screen_height)

        # 碰撞检测
        if self.check_wall_collision([self.player.x, self.player.y]):
            if keys[pg.K_w] or keys[pg.K_UP]:
                self.player.y += self.player.speed
            if keys[pg.K_s] or keys[pg.K_DOWN]:
                self.player.y -= self.player.speed
            if keys[pg.K_a] or keys[pg.K_LEFT]:
                self.player.x += self.player.speed
            if keys[pg.K_d] or keys[pg.K_RIGHT]:
                self.player.x -= self.player.speed

    def handle_room_switch(self):
        """处理房间切换"""
        if self.player.just_switched:
            if (self.wall_width < self.player.x < self.screen_width - self.wall_width and 
                self.wall_width < self.player.y < self.screen_height - self.wall_width):
                self.player.just_switched = False
            return

        current_room_data = self.get_current_room()
        px, py, pr = self.player.x, self.player.y, self.player.radius

        for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
            if gap_dir in ["left", "right"]:
                gap_x, gap_y_min, gap_y_max = gap_info
            elif gap_dir in ["top", "bottom"]:
                gap_x_min, gap_x_max, gap_y = gap_info

            target_room_id = self.room_neighbors.get(str(self.player.current_room), {}).get(gap_dir)
            if target_room_id is None:
                continue

            switch_triggered = False
            new_player_pos = [px, py]

            if gap_dir == "left" and px - pr <= gap_x and gap_y_min <= py <= gap_y_max:
                new_player_pos[0] = self.screen_width - self.wall_width - pr
                switch_triggered = True
            elif gap_dir == "right" and px + pr >= gap_x and gap_y_min <= py <= gap_y_max:
                new_player_pos[0] = self.wall_width + pr
                switch_triggered = True
            elif gap_dir == "top" and py - pr <= gap_y and gap_x_min <= px <= gap_x_max:
                new_player_pos[1] = self.screen_height - self.wall_width - pr
                switch_triggered = True
            elif gap_dir == "bottom" and py + pr >= gap_y and gap_x_min <= px <= gap_x_max:
                new_player_pos[1] = self.wall_width + pr
                switch_triggered = True

            if switch_triggered:
                prev_room_id = self.player.current_room
                
                # 更新玩家位置和房间
                self.player.x, self.player.y = new_player_pos
                self.player.current_room = target_room_id
                self.player.just_switched = True

                if target_room_id not in self.explored_rooms:
                    self.explored_rooms.append(target_room_id)
                    prev_x, prev_y = self.room_minimap_pos[prev_room_id]
                    cell_size = self.minimap.cell_size

                    if gap_dir == "left":
                        new_x, new_y = prev_x - cell_size, prev_y
                    elif gap_dir == "right":
                        new_x, new_y = prev_x + cell_size, prev_y
                    elif gap_dir == "top":
                        new_x, new_y = prev_x, prev_y - cell_size
                    else:
                        new_x, new_y = prev_x, prev_y + cell_size

                    self.room_minimap_pos[target_room_id] = (new_x, new_y)
                    
                    # 激活新房间的敌人
                    self.enemy_manager.activate_room(target_room_id)
                return

    def update_enemies(self):
        player_sprite = pg.sprite.Sprite()
        player_sprite.rect = self.get_player_rect()
        self.enemy_manager.update(player_sprite)

    def handle_bullet_collisions(self):
        for bullet in self.player.bullets[:]:
            bullet_rect = bullet.get_rect()
            hit_enemy = False
            for enemy in self.enemy_manager.get_active_enemies():
                if bullet_rect.colliderect(enemy.rect):
                    if hasattr(enemy, 'take_damage'):
                        enemy.take_damage(bullet.damage)
                    hit_enemy = True
                    break
            if hit_enemy:
                bullet.active = False
                self.player.bullets.remove(bullet)

    def handle_enemy_collisions(self):
        for enemy in self.enemy_manager.get_active_enemies():
            if self.get_player_rect().colliderect(enemy.rect):
                self.player.take_damage(10)

    def handle_fireball_collisions(self):
        for fireball in self.enemy_manager.get_projectiles():
            if self.get_player_rect().colliderect(fireball.rect):
                damage = fireball.hit_player(self.player)
                self.player.take_damage(damage)

    def update_items(self):
        item_message = self.item_manager.check_collisions(self.player, self.player.current_room)
        if item_message:
            if not isinstance(item_message, str):
                item_message = str(item_message)
            self.show_tip(item_message, 2)
        
        self.item_manager.update_traps()

    def get_current_room(self):
        return next(r for r in self.rooms_config["rooms"] if r["room_id"] == self.player.current_room)

    def check_chest_and_exit(self, gui_manager, restart_action, quit_action, settings_action):
        """检查宝箱和出口"""
        player_rect = self.get_player_rect()
        current_room_data = self.get_current_room()

        # 宝箱收集检测
        for chest in current_room_data.get("chests", []):
            if not chest["is_got"]:
                chest_rect = pg.Rect(chest["pos"][0] - 15, chest["pos"][1] - 15, 30, 30)
                if player_rect.colliderect(chest_rect):
                    chest["is_got"] = True
                    self.game_state["has_treasure"] = True
                    self.show_tip("Found the treasure! You can go to the exit!", 3)

        # 出口检测
        if self.player.current_room == 20 and current_room_data.get("is_exit"):
            exit_area = self.rooms_config["exit_detection"]
            exit_rect = pg.Rect(
                exit_area["x_min"],
                exit_area["y_min"],
                self.screen_width - exit_area["x_min"],
                exit_area["y_max"] - exit_area["y_min"]
            )

            if player_rect.colliderect(exit_rect):
                if self.game_state.get("has_treasure"):
                    gui_manager.victory = True
                    self.show_tip("You win!", 2)
                    gui_manager.show_end_buttons(
                        restart_action=restart_action,
                        quit_action=quit_action,
                        settings_action=settings_action
                    )
                    gui_manager.current_screen = "end"
                    return True
                else:
                    self.show_tip("Treasure not found yet!", 2)
        return False

    def update(self):
        """更新游戏状态"""
        self.handle_input()
        self.handle_room_switch()  # 确保这个被调用！
        self.update_enemies()
        self.handle_bullet_collisions()
        self.handle_enemy_collisions()
        self.handle_fireball_collisions()
        self.update_items()

    def is_player_dead(self):
        return not self.player.health_system.is_alive

    def restart_game(self):
        """重启游戏"""
        import os
        if os.path.exists('config/items_state.json'):
            os.remove('config/items_state.json')

        self.player, self.game_state, self.explored_rooms, self.room_minimap_pos = self.init_global_state()
        
        # 重新加载房间配置
        with open('config/rooms_config.json', 'r', encoding='utf-8') as f:
            self.rooms_config = json.load(f)
        self.rooms_config["rooms"] = [copy.deepcopy(room) for room in self.rooms_config["rooms"]]

        # 重置宝箱状态
        for room in self.rooms_config["rooms"]:
            for chest in room.get("chests", []):
                chest["is_got"] = False

        # 重新加载敌人和物品
        self.enemy_manager.rooms_config = self.rooms_config
        self.enemy_manager.load_all_rooms()
        self.enemy_manager.activate_room(self.player.current_room)
        self.item_manager = ItemManager(self.rooms_config)