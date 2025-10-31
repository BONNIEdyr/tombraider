import pygame as pg
import sys
import json
import copy


def load_config():
    with open('config/game_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


config = load_config()
WALL_WIDTH = config["game"]["wall_width"]
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600


def init_base_config():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("TombRaider")

    # 默认字体
    main_font = pg.font.Font(None, config["ui"]["fonts"]["main_font_size"])
    label_font = pg.font.Font(None, config["ui"]["fonts"]["label_font_size"])

    # 从配置加载颜色
    COLOR = {}
    for color_name, color_value in config["ui"]["colors"].items():
        COLOR[color_name] = tuple(color_value)

    return screen, main_font, label_font, COLOR


def init_global_state():
    player = {
        "pos": config["player"]["initial_pos"].copy(),
        "radius": config["player"]["radius"],
        "speed": config["player"]["speed"],
        "current_room": config["player"]["initial_room"],
        "just_switched": False
    }
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
    return pg.Rect(player["pos"][0] - player["radius"], player["pos"][1] - player["radius"],
                   player["radius"] * 2, player["radius"] * 2)


def show_tip(game_state, text, duration=None):
    if duration is None:
        duration = config["game"]["tip_duration"]
    game_state["tip_text"] = text
    game_state["tip_timer"] = duration * 60


def check_wall_collision(new_pos, player, current_room_data):
    player_rect = pg.Rect(new_pos[0] - player["radius"], new_pos[1] - player["radius"],
                          player["radius"] * 2, player["radius"] * 2)

    for wall in current_room_data["walls"]:
        wall_rect = pg.Rect(wall[0], wall[1], wall[2], wall[3])
        in_gap = False

        for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
            if gap_dir in ["left", "right"]:
                gap_x, gap_y_min, gap_y_max = gap_info
                if gap_dir == "right" and wall_rect.x == gap_x and gap_y_min <= new_pos[1] <= gap_y_max:
                    in_gap = True
                elif gap_dir == "left" and (wall_rect.x + wall_rect.width) == gap_x and gap_y_min <= new_pos[
                    1] <= gap_y_max:
                    in_gap = True
            elif gap_dir in ["top", "bottom"]:
                gap_x_min, gap_x_max, gap_y = gap_info
                if gap_dir == "top" and (wall_rect.y + wall_rect.height) == gap_y and gap_x_min <= new_pos[
                    0] <= gap_x_max:
                    in_gap = True
                elif gap_dir == "bottom" and wall_rect.y == gap_y and gap_x_min <= new_pos[0] <= gap_x_max:
                    in_gap = True
            if in_gap:
                break

        if not in_gap and player_rect.colliderect(wall_rect):
            return True
    return False


def handle_room_switch(player, current_room_data, room_neighbors, explored_rooms, room_minimap_pos, minimap):
    if player["just_switched"]:
        if WALL_WIDTH < player["pos"][0] < SCREEN_WIDTH - WALL_WIDTH and WALL_WIDTH < player["pos"][
            1] < SCREEN_HEIGHT - WALL_WIDTH:
            player["just_switched"] = False
        return

    px, py, pr = player["pos"][0], player["pos"][1], player["radius"]

    for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
        if gap_dir in ["left", "right"]:
            gap_x, gap_y_min, gap_y_max = gap_info
        elif gap_dir in ["top", "bottom"]:
            gap_x_min, gap_x_max, gap_y = gap_info

        target_room_id = room_neighbors.get(str(player["current_room"]), {}).get(gap_dir)
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
            prev_room_id = player["current_room"]
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
            return


def handle_chest_and_exit(player, current_room_data, game_state, rooms_config, screen, main_font, COLOR, draw_game):
    player_rect = get_player_rect(player)

    # 宝箱收集检测
    for chest in current_room_data.get("chests", []):
        if not chest["is_got"]:
            chest_rect = pg.Rect(chest["pos"][0] - 15, chest["pos"][1] - 15, 30, 30)
            if player_rect.colliderect(chest_rect):
                chest["is_got"] = True
                game_state["has_treasure"] = True
                show_tip(game_state, "获得宝箱！可以去出口了！", 3)

    if player["current_room"] == 20 and current_room_data.get("is_exit"):
        exit_area = rooms_config["exit_detection"]
        exit_rect = pg.Rect(
            exit_area["x_min"],
            exit_area["y_min"],
            SCREEN_WIDTH - exit_area["x_min"],
            exit_area["y_max"] - exit_area["y_min"]
        )

        if player_rect.colliderect(exit_rect):
            if game_state["has_treasure"]:
                show_tip(game_state, "你赢了！", 2)
                draw_game(screen, player, current_room_data, label_font, COLOR, minimap, room_neighbors,
                          room_minimap_pos, rooms_config)
                pg.display.flip()
                pg.time.wait(2000)
                pg.quit()
                sys.exit()
            else:
                show_tip(game_state, "还未找到宝藏！", 2)


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

    if player["current_room"] in room_rects:
        pg.draw.circle(screen, COLOR["RED"], room_rects[player["current_room"]].center, 3)


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


def draw_game(screen, player, current_room_data, label_font, COLOR, minimap, room_neighbors, room_minimap_pos, rooms_config):
    screen.fill(COLOR["WHITE"])

    for wall in current_room_data["walls"]:
        pg.draw.rect(screen, COLOR["BROWN"], (wall[0], wall[1], wall[2], wall[3]))

    if player["current_room"] == 1:
        entrance_rect = pg.Rect(0, 250, WALL_WIDTH, 100)
        pg.draw.rect(screen, COLOR["GREEN"], entrance_rect, 3)
        screen.blit(label_font.render("入口", True, COLOR["GREEN"]), (5, 280))

    for chest in current_room_data.get("chests", []):
        color = COLOR["BLUE"] if chest["is_got"] else COLOR["YELLOW"]
        pg.draw.circle(screen, color, chest["pos"], 15)

    if player["current_room"] == 20:
        exit_area = rooms_config["exit_detection"]
        pg.draw.rect(screen, COLOR["GREEN"],
                     (exit_area["x_min"], exit_area["y_min"],
                      SCREEN_WIDTH - exit_area["x_min"], exit_area["y_max"] - exit_area["y_min"]), 3)
        screen.blit(label_font.render("出口", True, COLOR["GREEN"]),
                    (exit_area["x_min"] + 10, exit_area["y_min"] + 10))

    pg.draw.circle(screen, COLOR["GREEN"], player["pos"], player["radius"])
    draw_minimap(screen, minimap, room_minimap_pos, room_neighbors, player, COLOR)

    if game_state["tip_timer"] > 0:
        tip_text = main_font.render(game_state["tip_text"], True, COLOR["BROWN"])
        tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        tip_bg_rect = tip_rect.inflate(20, 10)
        pg.draw.rect(screen, COLOR["WHITE"], tip_bg_rect)
        pg.draw.rect(screen, COLOR["BROWN"], tip_bg_rect, 2)
        screen.blit(tip_text, tip_rect)


def main():
    global screen, main_font, label_font, COLOR
    screen, main_font, label_font, COLOR = init_base_config()

    global player, game_state, explored_rooms, room_minimap_pos, minimap, room_neighbors
    player, game_state, explored_rooms, room_minimap_pos = init_global_state()
    minimap = init_minimap_config()

    with open('config/rooms_config.json', 'r', encoding='utf-8') as f:
        rooms_config = json.load(f)
    rooms_config["rooms"] = [copy.deepcopy(room) for room in rooms_config["rooms"]]
    room_neighbors = rooms_config["room_neighbors"]

    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            handle_minimap_drag(event, minimap)

        current_room = next(r for r in rooms_config["rooms"] if r["room_id"] == player["current_room"])

        keys = pg.key.get_pressed()
        spd = player["speed"]
        new_pos = list(player["pos"])

        if keys[pg.K_w] or keys[pg.K_UP]:
            new_pos[1] -= spd
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            new_pos[1] += spd
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            new_pos[0] -= spd
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            new_pos[0] += spd

        if 0 <= new_pos[0] <= SCREEN_WIDTH and 0 <= new_pos[1] <= SCREEN_HEIGHT:
            if not check_wall_collision(new_pos, player, current_room):
                player["pos"] = new_pos

        handle_room_switch(player, current_room, room_neighbors, explored_rooms, room_minimap_pos, minimap)
        handle_chest_and_exit(player, current_room, game_state, rooms_config, screen, main_font, COLOR, draw_game)

        if game_state["tip_timer"] > 0:
            game_state["tip_timer"] -= 1

        draw_game(screen, player, current_room, label_font, COLOR, minimap, room_neighbors, room_minimap_pos, rooms_config)
        pg.display.flip()
        clock.tick(60)

    pg.quit()


if __name__ == "__main__":
    main()