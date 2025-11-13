import pygame as pg
from src.audio import play_sound
from typing import Dict, List, Tuple

class GUIManager:
    def __init__(self, config: Dict):
        self.config = config
        self.colors = config["ui"]["colors"]
        self.fonts = {
            "main": pg.font.Font(None, config["ui"]["fonts"]["main_font_size"]), 
            "label": pg.font.Font(None, config["ui"]["fonts"]["label_font_size"]), 
            "title": pg.font.Font(None, 64)
        }

        self.screen_width = config["game"]["screen_width"]
        self.screen_height = config["game"]["screen_height"]
        self.wall_width = config["game"]["wall_width"]

        self.current_screen = "start" 
        self.buttons = []
        self.victory = False
        self._start_action = None
        self._quit_action = None
        self._settings_action = None
        self._restart_action = None
        self.previous_screen = None

        self.backgrounds = {}
        self.backgrounds["start"] = pg.image.load("assets/ui/start_background.jpg").convert()
        self.backgrounds["start"] = pg.transform.scale(self.backgrounds["start"], (self.screen_width, self.screen_height))
        self.backgrounds["end"] = pg.image.load("assets/ui/end_background.jpg").convert()
        self.backgrounds["end"] = pg.transform.scale(self.backgrounds["end"], (self.screen_width, self.screen_height))

        self.backgrounds["settings"] = pg.image.load("assets/ui/settings_background.jpg").convert()
        self.backgrounds["settings"] = pg.transform.scale(self.backgrounds["settings"], (self.screen_width, self.screen_height))

        try:
            self.icons = {
                "health": pg.image.load("assets/ui/heart_icon.png").convert_alpha(),
                "treasure": pg.image.load("assets/ui/treasure_icon.png").convert_alpha(),
            }
            for key in self.icons:
                self.icons[key] = pg.transform.scale(self.icons[key], (20, 20))
        except:
            self.icons = {}  

       
        self.raider_raw = pg.image.load("assets/raider.png").convert_alpha()
        self.treasure_raw = pg.image.load("assets/treasure.png").convert_alpha()

        try:
            self.treasure_find_raw = pg.image.load("assets/treasure_find.png").convert_alpha()
        except Exception:
            self.treasure_find_raw = None

        self.enemy_types = ["slime", "bat", "wizard", "guard"]
        self.enemy_display = {
            "slime": "Mummy",
            "bat": "Bat",
            "wizard": "Wizard",
            "guard": "Guard",
        }
    
        self.enemy_counts = {k: None for k in self.enemy_types}
        self.settings_callback = None
        self._start_action = None
        self._quit_action = None
        self._settings_action = None

        self._get_current_enemy_totals = lambda: {t: 0 for t in self.enemy_types}
    # This function draws the game scene including walls, player, enemies, items, and room features.
    def draw_game_screen(self, screen: pg.Surface, player, current_room_data, minimap, room_neighbors, room_minimap_pos, rooms_config, item_manager, enemy_manager=None):
        screen.fill(self.colors["WHITE"])

        for wall in current_room_data["walls"]:
            pg.draw.rect(screen, self.colors["BROWN"], (wall[0], wall[1], wall[2], wall[3]))

        current_room_id = self._get_player_room_id(player)
        
        if current_room_id == 1:
            entrance_rect = pg.Rect(0, 250, self.wall_width, 100)
            pg.draw.rect(screen, self.colors["GREEN"], entrance_rect, 3)
            screen.blit(self.fonts["label"].render("Entrance", True, self.colors["GREEN"]), (5, 280))

        for chest in current_room_data.get("chests", []):
            color = self.colors["BLUE"] if chest["is_got"] else self.colors["YELLOW"]
            img_to_use = None
            if chest.get("is_got"):
                img_to_use = getattr(self, 'treasure_find_raw', None) or getattr(self, 'treasure_raw', None)
            else:
                img_to_use = getattr(self, 'treasure_raw', None)

            if img_to_use is not None:
                try:
                    img = pg.transform.scale(img_to_use, (30, 30))
                    img_rect = img.get_rect(center=chest["pos"])
                    screen.blit(img, img_rect.topleft)
                except Exception:
                    pg.draw.circle(screen, color, chest["pos"], 15)
            else:
                pg.draw.circle(screen, color, chest["pos"], 15)

        if current_room_id == 20:
            exit_area = rooms_config["exit_detection"]
            pg.draw.rect(screen, self.colors["GREEN"],
                         (exit_area["x_min"], exit_area["y_min"],
                          self.screen_width - exit_area["x_min"], exit_area["y_max"] - exit_area["y_min"]), 3)
            screen.blit(self.fonts["label"].render("EXIT", True, self.colors["GREEN"]),
                        (exit_area["x_min"] + 10, exit_area["y_min"] + 10))
        
        if item_manager is not None:
            item_manager.draw_room_items(screen, current_room_id)

        if hasattr(player, 'draw'):
            player.draw(screen)
            player.draw_bullets(screen)
        else:
            if self.raider_raw is not None:
                try:
                    w = int(player["radius"] * 2 * 2.5)
                    h = int(player["radius"] * 2 * 2.5)
                    img = pg.transform.scale(self.raider_raw, (w, h))
                    img_rect = img.get_rect(center=player["pos"])
                    screen.blit(img, img_rect.topleft)
                except Exception:
                    pg.draw.circle(screen, self.colors["GREEN"], player["pos"], player["radius"])
            else:
                pg.draw.circle(screen, self.colors["GREEN"], player["pos"], player["radius"])

        minimap.draw(screen, room_minimap_pos, room_neighbors, player)
        
        if enemy_manager is not None:
            enemy_manager.draw(screen)

    # This function retrieves the player's rectangular area in a unified way.
    def _get_player_rect(self, player):
        if hasattr(player, 'get_rect'):
            return player.get_rect()
        else:
            return pg.Rect(player["pos"][0] - player["radius"], player["pos"][1] - player["radius"],
                           player["radius"] * 2, player["radius"] * 2)
        
    # This function retrieves the current room ID of the player in a unified way.
    def _get_player_room_id(self, player):
        return player.current_room if hasattr(player, 'current_room') else player["current_room"]
    
    # This function clears all buttons from the current button list.
    def clear_buttons(self):
        self.buttons = []

    # This function populates start screen buttons and remembers actions for later restore.
    def show_start_buttons(self, start_action, quit_action, settings_action=None):
        """Populate start screen buttons and remember actions for later restore."""
        self.clear_buttons()
        self._start_action = start_action
        self._quit_action = quit_action
        self._settings_action = settings_action
        self.create_button(x=300, y=300, width=200, height=50, text="START GAME", action=start_action, screen_name='start')
        if settings_action is not None:
            self.create_button(x=300, y=370, width=200, height=50, text="SETTINGS", action=settings_action, screen_name='start')
        self.create_button(x=300, y=440, width=200, height=50, text="EXIT", action=quit_action, screen_name='start')
    
    # This function populates end screen buttons with restart, settings and quit options.
    def show_end_buttons(self, restart_action, quit_action, settings_action=None):
        self._restart_action = restart_action
        self.clear_buttons()

        self.create_button(
            x=300, y=350, width=200, height=50,
            text="RESTART", action=restart_action, screen_name="end"
        )

        if settings_action is not None:
            self.create_button(
                x=300, y=420, width=200, height=50,
                text="SETTINGS", action=settings_action, screen_name="end"
            )

        self.create_button(
            x=300, y=490, width=200, height=50,
            text="EXIT", action=quit_action, screen_name="end"
        )

    # This function creates +/- buttons for enemy count adjustment and Save/Back buttons for settings screen.
    def show_settings_buttons(self):
        self.clear_buttons()
        start_x = 220
        start_y = 180
        row_h = 50
        label_w = 200
        btn_w = 40
        for i, t in enumerate(self.enemy_types):
            y = start_y + i * row_h
            def make_dec(tt):
                return lambda: self._adjust_enemy_count(tt, -1)
            def make_inc(tt):
                return lambda: self._adjust_enemy_count(tt, 1)
            self.create_button(x=start_x + label_w + 10, y=y, width=btn_w, height=36, text='-', action=make_dec(t), screen_name='settings')
            self.create_button(x=start_x + label_w + 10 + btn_w + 10, y=y, width=btn_w, height=36, text='+', action=make_inc(t), screen_name='settings')
        self.create_button(x=300, y=start_y + len(self.enemy_types) * row_h + 20, width=120, height=44, text='SAVE', action=self._save_settings, screen_name='settings')
        self.create_button(x=440, y=start_y + len(self.enemy_types) * row_h + 20, width=120, height=44, text='BACK', action=self._back_to_previous, screen_name='settings')

    # This helper function adjusts the count of a specific enemy type by a delta value.
    def _adjust_enemy_count(self, etype: str, delta: int) -> None:
        cur = self.enemy_counts.get(etype)
        if cur is None:
            cur = 0
        try:
            new = int(cur) + int(delta)
        except Exception:
            return
        if new < 0:
            new = 0
        self.enemy_counts[etype] = new

    # This helper function saves the current settings and returns to the previous screen.
    def _save_settings(self) -> None:
        if callable(self.settings_callback):
            try:
                self.settings_callback(dict(self.enemy_counts))
            except Exception:
                pass

        if self.previous_screen == "end":
            self.current_screen = "end"
            self.show_end_buttons(
                restart_action=self._restart_action,
                quit_action=self._quit_action,
                settings_action=self._settings_action
            )
        else:
            self.current_screen = "start"
            self.show_start_buttons(
                start_action=self._start_action,
                quit_action=self._quit_action,
                settings_action=self._settings_action
            )

    # This helper function returns to the previous screen from the settings screen.
    def _back_to_previous(self):
        if self.previous_screen is None:
            self.previous_screen = "start"

        self.current_screen = self.previous_screen

        if hasattr(self, 'on_screen_change_callback') and callable(self.on_screen_change_callback):
            self.on_screen_change_callback(self.current_screen)

        if self.previous_screen == "start":
            self.show_start_buttons(self._start_action, self._quit_action, self._settings_action)
        elif self.previous_screen == "end":
            self.show_end_buttons(
                restart_action=self._restart_action,
                quit_action=self._quit_action,
                settings_action=self._settings_action
            )

    # This function creates an interactive button with specified properties.
    def create_button(self, x: int, y: int, width: int, height: int, text: str, action, screen_name) -> None:
        self.buttons.append({
            "rect": pg.Rect(x, y, width, height),
            "text": text,
            "action": action,
            "hover": False,
            "screen": screen_name
        })

    # This function handles input events for button interactions.
    def handle_events(self, event: pg.event.Event) -> None:
        if self.current_screen in ["start", "end", "settings"]:
            mouse_pos = pg.mouse.get_pos()
            for btn in self.buttons:
                if btn["screen"] != self.current_screen:
                    continue

                btn["hover"] = btn["rect"].collidepoint(mouse_pos)

                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if btn["rect"].collidepoint(mouse_pos):
                        try:
                            play_sound('button')
                        except Exception:
                            pass
                        btn["action"]()

    # This function draws the start screen with title, buttons, and instructions.
    def draw_start_screen(self, screen: pg.Surface) -> None:
        if hasattr(self, 'backgrounds') and "start" in self.backgrounds and self.backgrounds["start"] is not None:
            screen.blit(self.backgrounds["start"], (0, 0))
        else:
            screen.fill(self.colors["DARK_BROWN"])

        overlay = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        title = self.fonts["title"].render("Tomb Raider: Maze Adventure", True, self.colors["GOLD"])
        screen.blit(title, (self.screen_width//2 - title.get_width()//2, 150))

        for btn in self.buttons:
            if btn.get("screen") == "start":
                color = self.colors["LIGHT_BROWN"] if btn["hover"] else self.colors["BROWN"]
                pg.draw.rect(screen, color, btn["rect"], border_radius=10)
                pg.draw.rect(screen, self.colors["BLACK"], btn["rect"], 2, border_radius=10)
                text_surf = self.fonts["label"].render(btn["text"], True, self.colors["WHITE"])
                screen.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))

        tips = ["Arrow keys to move | Space to shoot | Mouse to move minimap", "Find the treasure and reach the exit to win"]
        for i, tip in enumerate(tips):
            text = self.fonts["label"].render(tip, True, self.colors["WHITE"])
            screen.blit(text, (self.screen_width//2 - text.get_width()//2, 500 + i*30))

    # This function draws the in-game HUD displaying health, ammo, room info, and temporary tips.
    def draw_hud(self, screen: pg.Surface, player, game_state: Dict) -> None:
        if player is None or game_state is None:
            return

        tip_text_content = game_state.get("tip_text", "")
        if tip_text_content is None:
            tip_text_content = ""
        elif not isinstance(tip_text_content, str):
            tip_text_content = str(tip_text_content)

        try:
            if game_state.get("tip_timer", 0) > 0:
                game_state["tip_timer"] = max(0, game_state.get("tip_timer", 0) - 1)
                if game_state["tip_timer"] == 0:
                    game_state["tip_text"] = ""
        except Exception:
            pass
            
        health_bg = pg.Rect(20, 10, 200, 8)
        pg.draw.rect(screen, self.colors["RED"], health_bg)

        if hasattr(player, 'health_system') and player.health_system is not None:
            health_percentage = player.health_system.current_health / player.health_system.max_health
            pg.draw.rect(screen, self.colors["GREEN"], 
                        (20, 10, 200 * health_percentage, 8))

            health_text = self.fonts["main"].render(
                f"HP: {player.health_system.current_health}/{player.health_system.max_health}", 
                True, self.colors["BLACK"])
            screen.blit(health_text, (230, 8))
        else:

            health_text = self.fonts["main"].render("Health:  ?/?", True, self.colors["BLACK"])
            screen.blit(health_text, (230, 0))

        ammo_count = getattr(player, 'ammo', 0)
        ammo_text = self.fonts["main"].render(f"Ammo: {ammo_count}", True, self.colors["BLACK"])
        screen.blit(ammo_text, (20, 25))

        room_text = self.fonts["main"].render(
            f"Room: {getattr(player, 'current_room', '?')}/20", True, self.colors["BLACK"])
        screen.blit(room_text, (120, 25))  

        treasure_text = "Treasure Found" if game_state.get("has_treasure", False) else "Treasure Not Found"
        treasure_color = self.colors["GOLD"] if game_state.get("has_treasure", False) else self.colors["RED"]
        screen.blit(self.fonts["main"].render(treasure_text, True, treasure_color), (480, 18))

        if game_state.get("tip_timer", 0) > 0:
            tip_bg = pg.Rect(200, 300, 400, 50)
            pg.draw.rect(screen, self.colors["WHITE"], tip_bg)
            pg.draw.rect(screen, self.colors["BROWN"], tip_bg, 2)

            tip_surface = self.fonts["main"].render(tip_text_content, True, self.colors["BROWN"])
            screen.blit(tip_surface, tip_surface.get_rect(center=tip_bg.center))

    # This function draws the end screen with victory/defeat message and buttons.
    def draw_end_screen(self, screen: pg.Surface) -> None:
        if hasattr(self, 'backgrounds') and "end" in self.backgrounds and self.backgrounds["end"] is not None:
            screen.blit(self.backgrounds["end"], (0, 0))
        else:
            screen.fill(self.colors["DARK_BROWN"])

        overlay = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        result = "Victory! Successfully escaped!" if self.victory else "Defeat! Try again!"
        result_color = self.colors["GOLD"] if self.victory else self.colors["RED"]
        result_text = self.fonts["title"].render(result, True, result_color)
        screen.blit(result_text, (self.screen_width//2 - result_text.get_width()//2, 150))

        for btn in self.buttons:
            if btn.get("screen") == "end":
                color = self.colors["LIGHT_BROWN"] if btn["hover"] else self.colors["BROWN"]
                pg.draw.rect(screen, color, btn["rect"], border_radius=10)
                pg.draw.rect(screen, self.colors["BLACK"], btn["rect"], 2, border_radius=10)
                text_surf = self.fonts["label"].render(btn["text"], True, self.colors["WHITE"])
                screen.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))
    # This function draws the appropriate screen based on the current screen state.
    def draw(self, screen: pg.Surface, player=None, game_state=None, 
         current_room_data=None, minimap=None, room_neighbors=None, 
         room_minimap_pos=None, rooms_config=None, item_manager=None, 
         enemy_manager=None) -> None:
        if self.current_screen == "start":
            self.draw_start_screen(screen)
        elif self.current_screen == "settings":
            self.draw_settings_screen(screen)
        elif self.current_screen == "game":

            if all([current_room_data, minimap, room_neighbors, room_minimap_pos, rooms_config]):
                self.draw_game_screen(screen, player, current_room_data, minimap, 
                                    room_neighbors, room_minimap_pos, rooms_config, 
                                    item_manager, enemy_manager)
            
            if player is not None and game_state is not None:
                self.draw_hud(screen, player, game_state)
            else:
                screen.fill(self.colors["WHITE"])
                warning_text = self.fonts["main"].render("Loading game...", True, self.colors["BLACK"])
                screen.blit(warning_text, (self.screen_width//2 - warning_text.get_width()//2, self.screen_height//2))
        elif self.current_screen == "end":
            self.draw_end_screen(screen)

    # This function draws the settings screen with enemy count controls and total display.      
    def draw_settings_screen(self, screen: pg.Surface) -> None:
        """Draw the settings screen with per-enemy count controls and total."""
        if hasattr(self, 'backgrounds') and "settings" in self.backgrounds and self.backgrounds["settings"] is not None:
            screen.blit(self.backgrounds["settings"], (0, 0))
        else:
            screen.fill(self.colors["DARK_BROWN"])

        overlay = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        title = self.fonts["title"].render("Settings", True, self.colors["GOLD"])
        screen.blit(title, (self.screen_width//2 - title.get_width()//2, 80))

        start_x = 220
        start_y = 180
        row_h = 50

        for i, t in enumerate(self.enemy_types):
            y = start_y + i * row_h

            val = self.enemy_counts.get(t)
            val_text = "0" if val is None else str(val)

            display_name = self.enemy_display.get(t, t).capitalize()
            label_text = f"{display_name}: {val_text}"
            label = self.fonts["label"].render(label_text, True, self.colors["WHITE"])
            screen.blit(label, (start_x, y))

        # total count display
        total = 0
        for v in self.enemy_counts.values():
            if v is not None:
                try:
                    total += int(v)
                except Exception:
                    pass

        total_surf = self.fonts["main"].render(f"Total enemies: {total}", True, self.colors["WHITE"])
        screen.blit(total_surf, (start_x, start_y + len(self.enemy_types) * row_h + 80))

        # draw settings buttons
        for btn in self.buttons:
            if btn.get("screen") == "settings":
                color = self.colors["LIGHT_BROWN"] if btn["hover"] else self.colors["BROWN"]
                pg.draw.rect(screen, color, btn["rect"], border_radius=6)
                pg.draw.rect(screen, self.colors["BLACK"], btn["rect"], 2, border_radius=6)
                text_surf = self.fonts["label"].render(btn["text"], True, self.colors["WHITE"])
                screen.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))

    # This function sets the callback for enemy randomization settings.
    def set_settings_callback(self, callback):
        self.settings_callback = callback

    # This function initializes enemy count display based on game manager data.
    def init_enemy_counts(self, game_manager):
        current_totals = game_manager.get_current_enemy_totals()
        self.enemy_counts = {t: current_totals.get(t, 0) for t in self.enemy_types}