import pygame as pg
import sys
import json
import copy
import random

from src.enemies.enemy_manager import EnemyManager
from src.player.player import Player
from src.gui.gui_manager import GUIManager
from src.items.item_manager import ItemManager


def load_config():
    with open('config/game_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


config = load_config()
WALL_WIDTH = config["game"]["wall_width"]
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

def init_base_config(config):
    """初始化屏幕、字体等基础配置"""
    # 注意：pg.init() 现在在 main() 函数开头调用
    
    # 从game节点获取屏幕尺寸
    SCREEN_WIDTH = config["game"]["screen_width"]
    SCREEN_HEIGHT = config["game"]["screen_height"]
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("古墓丽影：迷宫探险")
    
    # 加载字体（使用ui节点的字体大小）
    main_font = pg.font.SysFont(None, config["ui"]["fonts"]["main_font_size"])
    label_font = pg.font.SysFont(None, config["ui"]["fonts"]["label_font_size"])
    
    # 返回颜色配置（从ui节点获取）
    COLOR = config["ui"]["colors"]
    
    return screen, main_font, label_font, COLOR




def init_global_state():
    # 使用新的Player类
    player = Player(
        config["player"]["initial_pos"][0],
        config["player"]["initial_pos"][1]
    )
    player.current_room = config["player"]["initial_room"]
    player.just_switched = False
    
    game_state = {"has_treasure": False, "tip_text": "", "tip_timer": 0}
    explored_rooms = [config["player"]["initial_room"]]
    room_minimap_pos = {config["player"]["initial_room"]: (0, 0)}
    return player, game_state, explored_rooms, room_minimap_pos


def init_minimap_config():
    minimap_config = config["minimap"]
    return {
        "w": minimap_config["width"],
        "h": minimap_config["height"],
        "x": minimap_config["x"],
        "y": minimap_config["y"],
        "cell_size": minimap_config["cell_size"],
        "is_dragging": False,
        "drag_off_x": 0,
        "drag_off_y": 0
    }


def get_player_rect(player):
    # 兼容字典和对象两种形式
    if hasattr(player, 'get_rect'):
        return player.get_rect()
    else:
        return pg.Rect(player["pos"][0] - player["radius"], player["pos"][1] - player["radius"],
                       player["radius"] * 2, player["radius"] * 2)


def get_player_room_id(player):
    """统一获取玩家房间ID"""
    return player.current_room if hasattr(player, 'current_room') else player["current_room"]


def get_player_position(player):
    """统一获取玩家位置"""
    if hasattr(player, 'x'):
        return [player.x, player.y]
    else:
        return player["pos"]


def get_player_radius(player):
    """统一获取玩家半径"""
    return player.radius if hasattr(player, 'radius') else player["radius"]


def show_tip(game_state, text, duration=None):
    if duration is None:
        duration = config["game"]["tip_duration"]
    
     # 确保 text 是字符串类型
    if text is None:
        text = ""
    elif not isinstance(text, str):
        text = str(text)

    game_state["tip_text"] = text
    game_state["tip_timer"] = duration * 60


def check_wall_collision(new_pos, player, current_room_data):
    # 兼容字典和对象两种形式
    if hasattr(player, 'radius'):
        radius = player.radius
    else:
        radius = player["radius"]
        
    player_rect = pg.Rect(new_pos[0] - radius, new_pos[1] - radius,
                          radius * 2, radius * 2)

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


def handle_room_switch(player, current_room_data, room_neighbors, explored_rooms, room_minimap_pos, minimap, enemy_manager=None):
    # 兼容字典和对象两种形式
    if hasattr(player, 'just_switched'):
        just_switched = player.just_switched
        current_room = player.current_room
        pos = [player.x, player.y]
        radius = player.radius
    else:
        just_switched = player["just_switched"]
        current_room = player["current_room"]
        pos = player["pos"]
        radius = player["radius"]
    
    if just_switched:
        if WALL_WIDTH < pos[0] < SCREEN_WIDTH - WALL_WIDTH and WALL_WIDTH < pos[1] < SCREEN_HEIGHT - WALL_WIDTH:
            if hasattr(player, 'just_switched'):
                player.just_switched = False
            else:
                player["just_switched"] = False
        return

    px, py, pr = pos[0], pos[1], radius

    for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
        if gap_dir in ["left", "right"]:
            gap_x, gap_y_min, gap_y_max = gap_info
        elif gap_dir in ["top", "bottom"]:
            gap_x_min, gap_x_max, gap_y = gap_info

        target_room_id = room_neighbors.get(str(current_room), {}).get(gap_dir)
        if target_room_id is None:
            continue

        switch_triggered = False
        new_player_pos = [px, py]

        if gap_dir == "left" and px - pr <= gap_x and gap_y_min <= py <= gap_y_max:
            new_player_pos[0] = SCREEN_WIDTH - WALL_WIDTH - pr
            switch_triggered = True
        elif gap_dir == "right" and px + pr >= gap_x and gap_y_min <= py <= gap_y_max:
            new_player_pos[0] = WALL_WIDTH + pr
            switch_triggered = True
        elif gap_dir == "top" and py - pr <= gap_y and gap_x_min <= px <= gap_x_max:
            new_player_pos[1] = SCREEN_HEIGHT - WALL_WIDTH - pr
            switch_triggered = True
        elif gap_dir == "bottom" and py + pr >= gap_y and gap_x_min <= px <= gap_x_max:
            new_player_pos[1] = WALL_WIDTH + pr
            switch_triggered = True

        if switch_triggered:
            prev_room_id = current_room
            
            # 更新玩家位置和房间
            if hasattr(player, 'x'):
                player.x, player.y = new_player_pos
                player.current_room = target_room_id
                player.just_switched = True
            else:
                player["pos"] = new_player_pos
                player["current_room"] = target_room_id
                player["just_switched"] = True

            if target_room_id not in explored_rooms:
                explored_rooms.append(target_room_id)
                prev_x, prev_y = room_minimap_pos[prev_room_id]
                cell_size = minimap["cell_size"]

                if gap_dir == "left":
                    new_x, new_y = prev_x - cell_size, prev_y
                elif gap_dir == "right":
                    new_x, new_y = prev_x + cell_size, prev_y
                elif gap_dir == "top":
                    new_x, new_y = prev_x, prev_y - cell_size
                else:
                    new_x, new_y = prev_x, prev_y + cell_size

                room_minimap_pos[target_room_id] = (new_x, new_y)
                # Activate enemy group for the new room if manager provided
                if enemy_manager is not None:
                    try:
                        enemy_manager.activate_room(target_room_id)
                    except Exception:
                        pass
            return


def handle_chest_and_exit(player, current_room_data, game_state, rooms_config, screen, main_font, COLOR, draw_game,
                          gui_manager, restart_action, quit_action, settings_action, item_manager=None):
    player_rect = get_player_rect(player)
    current_room_id = get_player_room_id(player)

    # 宝箱收集检测（保持不变）
    for chest in current_room_data.get("chests", []):
        if not chest["is_got"]:
            chest_rect = pg.Rect(chest["pos"][0] - 15, chest["pos"][1] - 15, 30, 30)
            if player_rect.colliderect(chest_rect):
                chest["is_got"] = True
                game_state["has_treasure"] = True
                show_tip(game_state, "Found the treasure! You can go to the exit!", 3)

    if current_room_id == 20 and current_room_data.get("is_exit"):
        exit_area = rooms_config["exit_detection"]
        exit_rect = pg.Rect(
            exit_area["x_min"],
            exit_area["y_min"],
            SCREEN_WIDTH - exit_area["x_min"],
            exit_area["y_max"] - exit_area["y_min"]
        )

        if player_rect.colliderect(exit_rect):
            if game_state.get("has_treasure"):

                gui_manager.victory = True
                show_tip(game_state, "You win!", 2)


                gui_manager.show_end_buttons(
                    restart_action=restart_action,
                    quit_action=quit_action,
                    settings_action=settings_action
                )


                gui_manager.current_screen = "end"
                return
            else:
                show_tip(game_state, "Treasure not found yet!", 2)



def draw_minimap(screen, minimap, room_minimap_pos, room_neighbors, player, COLOR):
    minimap_rect = pg.Rect(minimap["x"], minimap["y"], minimap["w"], minimap["h"])
    pg.draw.rect(screen, COLOR["GRAY"], minimap_rect)
    pg.draw.rect(screen, COLOR["BLACK"], minimap_rect, 2)

    if not room_minimap_pos:
        return

    all_x = [pos[0] for pos in room_minimap_pos.values()]
    all_y = [pos[1] for pos in room_minimap_pos.values()]
    min_x, max_x, min_y, max_y = min(all_x), max(all_x), min(all_y), max(all_y)

    offset_x = minimap["x"] + (minimap["w"] - (max_x - min_x + minimap["cell_size"])) // 2
    offset_y = minimap["y"] + (minimap["h"] - (max_y - min_y + minimap["cell_size"])) // 2

    room_rects = {}
    for room_id, (rel_x, rel_y) in room_minimap_pos.items():
        draw_x = offset_x + (rel_x - min_x)
        draw_y = offset_y + (rel_y - min_y)
        room_rect = pg.Rect(draw_x, draw_y, minimap["cell_size"], minimap["cell_size"])
        pg.draw.rect(screen, COLOR["LIGHT_GRAY"], room_rect)
        pg.draw.rect(screen, COLOR["BLACK"], room_rect, 1)
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
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midright, neighbor_rect.midleft, 2)
            elif direction == "left":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midleft, neighbor_rect.midright, 2)
            elif direction == "top":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midtop, neighbor_rect.midbottom, 2)
            elif direction == "bottom":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midbottom, neighbor_rect.midtop, 2)

    current_room_id = get_player_room_id(player)
    if current_room_id in room_rects:
        pg.draw.circle(screen, COLOR["RED"], room_rects[current_room_id].center, 3)


def handle_minimap_drag(event, minimap):
    if event.type == pg.MOUSEBUTTONDOWN:
        minimap_rect = pg.Rect(minimap["x"], minimap["y"], minimap["w"], minimap["h"])
        if minimap_rect.collidepoint(event.pos):
            minimap["is_dragging"] = True
            minimap["drag_off_x"] = event.pos[0] - minimap["x"]
            minimap["drag_off_y"] = event.pos[1] - minimap["y"]
    elif event.type == pg.MOUSEBUTTONUP:
        minimap["is_dragging"] = False
    elif event.type == pg.MOUSEMOTION and minimap["is_dragging"]:
        new_x = event.pos[0] - minimap["drag_off_x"]
        new_y = event.pos[1] - minimap["drag_off_y"]
        minimap["x"] = max(0, min(new_x, SCREEN_WIDTH - minimap["w"]))
        minimap["y"] = max(0, min(new_y, SCREEN_HEIGHT - minimap["h"]))


def draw_game(screen, player, current_room_data, label_font, COLOR, minimap, room_neighbors, room_minimap_pos, rooms_config, item_manager):
    screen.fill(COLOR["WHITE"])


    for wall in current_room_data["walls"]:
        pg.draw.rect(screen, COLOR["BROWN"], (wall[0], wall[1], wall[2], wall[3]))

    current_room_id = get_player_room_id(player)
    
    if current_room_id == 1:
        entrance_rect = pg.Rect(0, 250, WALL_WIDTH, 100)
        pg.draw.rect(screen, COLOR["GREEN"], entrance_rect, 3)
        screen.blit(label_font.render("Entrance", True, COLOR["GREEN"]), (5, 280))

    for chest in current_room_data.get("chests", []):
        color = COLOR["BLUE"] if chest["is_got"] else COLOR["YELLOW"]
        pg.draw.circle(screen, color, chest["pos"], 15)

    if current_room_id == 20:
        exit_area = rooms_config["exit_detection"]
        pg.draw.rect(screen, COLOR["GREEN"],
                     (exit_area["x_min"], exit_area["y_min"],
                      SCREEN_WIDTH - exit_area["x_min"], exit_area["y_max"] - exit_area["y_min"]), 3)
        screen.blit(label_font.render("EXIT", True, COLOR["GREEN"]),
                    (exit_area["x_min"] + 10, exit_area["y_min"] + 10))
        
     # 绘制物品
    if item_manager is not None:
        item_manager.draw_room_items(screen, current_room_id)

    # 绘制玩家（兼容对象和字典）
    if hasattr(player, 'draw'):
        player.draw(screen)
        player.draw_bullets(screen)  # 绘制子弹
    else:
        pg.draw.circle(screen, COLOR["GREEN"], player["pos"], player["radius"])

    draw_minimap(screen, minimap, room_minimap_pos, room_neighbors, player, COLOR)



def main():
    config = load_config()
    
    # 第一步：先初始化Pygame
    pg.init()  # 确保在所有GUI组件创建之前初始化
    
    # 设置自定义窗口图标 - 在这里修改
    try:
        icon = pg.image.load("assets/ui/window_icon.png")  # 修改这个路径
        pg.display.set_icon(icon)
    except:
        print("Warning: Could not load window icon")
    
    # 第二步：初始化基础配置
    global screen, main_font, label_font, COLOR
    screen, main_font, label_font, COLOR = init_base_config(config)

    # 第三步：现在创建GUI管理器（此时Pygame已初始化）
    gui_manager = GUIManager(config)

    # 其他初始化逻辑保持不变
    global player, game_state, explored_rooms, room_minimap_pos, minimap, room_neighbors
    player, game_state, explored_rooms, room_minimap_pos = init_global_state()
    minimap = init_minimap_config()

    with open('config/rooms_config.json', 'r', encoding='utf-8') as f:
        rooms_config = json.load(f)
    rooms_config["rooms"] = [copy.deepcopy(room) for room in rooms_config["rooms"]]
    room_neighbors = rooms_config["room_neighbors"]

    # 敌人管理器初始化
    enemy_manager = EnemyManager(rooms_config)
    enemy_manager.load_all_rooms()
    enemy_manager.activate_room(player.current_room)

     # 新增：物品管理器初始化
    item_manager = ItemManager(rooms_config)

    # settings save callback: apply counts, persist rooms_config, and reload EnemyManager
    def _apply_settings_and_reload(counts):
        # counts: mapping etype -> int (desired total across all rooms)
        desired = {k.lower(): (None if v is None else int(v)) for k, v in (counts or {}).items()}

        # current totals per type
        current = {t: 0 for t in gui_manager.enemy_types}
        for room in rooms_config.get("rooms", []):
            for e in room.get("enemies", []):
                et = (e.get("type") or "").lower()
                if et in current:
                    current[et] += 1

        # For each type, compute diff and add/remove accordingly.
        for etype in gui_manager.enemy_types:
            d = desired.get(etype)
            if d is None:
                continue
            need = d - current.get(etype, 0)
            if need > 0:
                # add to rooms with fewer enemies first
                rooms = rooms_config.get("rooms", [])
                rooms_sorted = sorted(rooms, key=lambda r: len(r.get("enemies", [])))
                # 如果要添加的数量少于房间数，则按权重从所有房间中随机选择不重复房间，避免总是填充前面的房间
                if need < len(rooms_sorted):
                    # 使用 Efraimidis–Spirakis 加权无放回采样，从所有房间中按权重抽取不重复房间
                    rooms_all = rooms_sorted
                    counts = [len(r.get("enemies", [])) for r in rooms_all]
                    maxc = max(counts) if counts else 0
                    # 权重：越少敌人的房间权重越高
                    weights = [maxc - c + 1 for c in counts]

                    # 生成随机键 key = U^(1/w)（w>0），取最大的 k 个索引
                    keys = []
                    for idx, w in enumerate(weights):
                        try:
                            if w <= 0:
                                key = 0.0
                            else:
                                key = random.random() ** (1.0 / float(w))
                        except Exception:
                            key = random.random()
                        keys.append((key, idx))

                    # 选取拥有最大 key 值的 need 个索引（无放回）
                    keys.sort(reverse=True)
                    chosen_idxs = [idx for (_, idx) in keys[:need]]
                    for i, idx in enumerate(chosen_idxs):
                        room = rooms_all[idx]
                        offset_x = 60 + (i % 5) * 20
                        offset_y = 60 + (i % 3) * 20
                        room.setdefault("enemies", []).append({"type": etype, "pos": [offset_x, offset_y], "hp": 1, "speed": 1})
                    need = 0
                else:
                    ri = 0
                    while need > 0 and rooms_sorted:
                        room = rooms_sorted[ri % len(rooms_sorted)]
                        offset_x = 60 + ((ri // len(rooms_sorted)) % 5) * 20
                        offset_y = 60 + (ri % 3) * 20
                        room.setdefault("enemies", []).append({"type": etype, "pos": [offset_x, offset_y], "hp": 1, "speed": 1})
                        need -= 1
                        ri += 1
            elif need < 0:
                # remove from rooms with most enemies first
                to_remove = -need
                rooms_sorted_desc = sorted(rooms_config.get("rooms", []), key=lambda r: len(r.get("enemies", [])), reverse=True)
                for room in rooms_sorted_desc:
                    if to_remove <= 0:
                        break
                    new_list = []
                    for e in room.get("enemies", []):
                        if to_remove > 0 and (e.get("type") or "").lower() == etype:
                            to_remove -= 1
                            continue
                        new_list.append(e)
                    room["enemies"] = new_list

        # persist changes
        try:
            with open('config/rooms_config.json', 'w', encoding='utf-8') as wf:
                json.dump(rooms_config, wf, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write rooms_config.json: {e}")

        # reload enemy manager groups
        enemy_manager.rooms_config = rooms_config
        enemy_manager.all_enemies.clear()
        enemy_manager.projectiles.empty()
        enemy_manager.active_group = pg.sprite.Group()
        enemy_manager.active_room_id = None
        enemy_manager.load_all_rooms()
        enemy_manager.activate_room(player.current_room)

    gui_manager.settings_callback = _apply_settings_and_reload

    # 第四步：创建开始界面按钮
    def _game():
        gui_manager.current_screen = "game"
        enemy_manager.activate_room(player.current_room)
    
    def quit_game():
        pg.quit()
        sys.exit()
    
    def _open_settings():
        # 统计敌人总数，初始化设置界面值
        totals = {t: 0 for t in gui_manager.enemy_types}
        for room in rooms_config.get("rooms", []):
            for e in room.get("enemies", []):
                et = (e.get("type") or "").lower()
                if et in totals:
                    totals[et] += 1

        gui_manager.enemy_counts.update(totals)

        gui_manager.previous_screen = gui_manager.current_screen
        gui_manager.current_screen = "settings"
        gui_manager.show_settings_buttons()
    def _open_settings_from_end():
        _open_settings()



    # populate start screen buttons via GUIManager helper
    gui_manager.show_start_buttons(start_action=_game, quit_action=quit_game, settings_action=_open_settings)
    
    def restart_game():
        global player, game_state, explored_rooms, room_minimap_pos, rooms_config, item_manager
        print("[DEBUG] Restart button clicked!")

        # 删除旧的物品存档文件
        import os
        if os.path.exists('config/items_state.json'):
            os.remove('config/items_state.json')
            print("[DEBUG] items_state.json 已删除，旧物品存档已清空。")

        # 重置玩家与全局状态
        player, game_state, explored_rooms, room_minimap_pos = init_global_state()

        # 重新加载房间配置（地图蓝图）
        with open('config/rooms_config.json', 'r', encoding='utf-8') as f:
            rooms_config = json.load(f)
        rooms_config["rooms"] = [copy.deepcopy(room) for room in rooms_config["rooms"]]

        # 重置宝箱状态
        for room in rooms_config["rooms"]:
            for chest in room.get("chests", []):
                chest["is_got"] = False

        # 重新加载敌人
        enemy_manager.rooms_config = rooms_config
        enemy_manager.load_all_rooms()
        enemy_manager.activate_room(player.current_room)

        # 重新创建 ItemManager（此时文件已被删除，会自动新建干净状态）
        item_manager = ItemManager(rooms_config)
        print("[DEBUG] 全新 ItemManager 已创建。")

        # 恢复游戏界面
        gui_manager.victory = False
        gui_manager.current_screen = "game"

        print("[DEBUG] Restart complete, 全新局面已加载。")




    


    clock = pg.time.Clock()
    running = True

    while running:
        # 根据当前界面状态处理不同逻辑
        if gui_manager.current_screen == "start":
            # 开始界面逻辑
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                gui_manager.handle_events(event)
            
            gui_manager.draw(screen)
            pg.display.flip()
            clock.tick(60)
            continue
        
        elif gui_manager.current_screen == "settings":
            # 设置界面：处理事件并让 GUIManager 处理点击
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                gui_manager.handle_events(event)

            gui_manager.draw(screen)
            pg.display.flip()
            clock.tick(60)
            continue

        elif gui_manager.current_screen == "game":
            # 游戏主逻辑（原来的游戏循环）

             # 新增：物品碰撞检测
            item_message = item_manager.check_collisions(player, player.current_room)
            if item_message:

                if not isinstance(item_message, str):
                    item_message = str(item_message)

                show_tip(game_state, item_message, 2)
        
            # 新增：更新陷阱状态
            item_manager.update_traps()

            current_room = next(r for r in rooms_config["rooms"] if r["room_id"] == player.current_room)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        player.shoot()
                handle_minimap_drag(event, minimap)

            keys = pg.key.get_pressed()
            player.update(keys, SCREEN_WIDTH, SCREEN_HEIGHT)

            # 碰撞检测
            if check_wall_collision([player.x, player.y], player, current_room):
                if keys[pg.K_w] or keys[pg.K_UP]:
                    player.y += player.speed
                if keys[pg.K_s] or keys[pg.K_DOWN]:
                    player.y -= player.speed
                if keys[pg.K_a] or keys[pg.K_LEFT]:
                    player.x += player.speed
                if keys[pg.K_d] or keys[pg.K_RIGHT]:
                    player.x -= player.speed

            handle_room_switch(player, current_room, room_neighbors, explored_rooms, room_minimap_pos, minimap, enemy_manager)
            
            # 更新敌人和投射物
            player_sprite = pg.sprite.Sprite()
            player_sprite.rect = get_player_rect(player)
            enemy_manager.update(player_sprite)
            
            # 子弹与敌人碰撞检测
            for bullet in player.bullets[:]:
                bullet_rect = bullet.get_rect()
                hit_enemy = False
                for enemy in enemy_manager.get_active_enemies():
                    if bullet_rect.colliderect(enemy.rect):
                        if hasattr(enemy, 'take_damage'):
                            enemy.take_damage(bullet.damage)
                        hit_enemy = True
                        break
                if hit_enemy:
                    bullet.active = False
                    player.bullets.remove(bullet)
            
            # 敌人与玩家碰撞检测
            for enemy in enemy_manager.get_active_enemies():
                if get_player_rect(player).colliderect(enemy.rect):
                    player.take_damage(10)
            
            # 火球与玩家碰撞检测
            for fireball in enemy_manager.get_projectiles():
                if get_player_rect(player).colliderect(fireball.rect):
                    damage = fireball.hit_player(player)
                    player.take_damage(damage)
            if not player.health_system.is_alive:
                show_tip(game_state, "You Died!", 1)
                draw_game(screen, player, current_room, label_font, COLOR, minimap, room_neighbors, room_minimap_pos, rooms_config, item_manager)
                gui_manager.draw(screen, player, game_state)  # 让HUD绘制tip
                pg.display.flip()
                pg.time.wait(1000)
                gui_manager.victory = False
                gui_manager.show_end_buttons(
                    restart_action=restart_game,
                    quit_action=quit_game,
                    settings_action=_open_settings_from_end
                )
                gui_manager.current_screen = "end"
                continue

            
            handle_chest_and_exit(
                player, current_room, game_state, rooms_config, screen, main_font, COLOR, draw_game,
                gui_manager,
                restart_action=restart_game,
                quit_action=quit_game,
                settings_action=_open_settings_from_end,
                item_manager=item_manager
            )

            draw_game(screen, player, current_room, label_font, COLOR, minimap, room_neighbors, room_minimap_pos, rooms_config, item_manager)
            enemy_manager.draw(screen)
            
            gui_manager.draw(screen, player, game_state)
            
            pg.display.flip()
            clock.tick(60)
        elif gui_manager.current_screen == "end":
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                gui_manager.handle_events(event)
            gui_manager.draw(screen)
            pg.display.flip()
            clock.tick(60)
            continue
    item_manager.save_state()
    pg.quit()


if __name__ == "__main__":
    main()
