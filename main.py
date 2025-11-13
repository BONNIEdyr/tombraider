import pygame as pg
import sys
import json
import random  
from src.game_manager import GameManager
from src.gui.gui_manager import GUIManager

BGM_CHANNEL = 0  

def load_config():
    """Load game configuration from JSON file"""
    with open('config/game_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def init_audio(config):
    """Initialize audio system and load BGM files"""
    pg.mixer.init()
    bgm = {}
    try:
        bgm['start'] = pg.mixer.Sound(config['bgm']['start'])
        bgm['settings'] = pg.mixer.Sound(config['bgm']['settings'])
        bgm['game'] = pg.mixer.Sound(config['bgm']['game'])
        bgm['win'] = pg.mixer.Sound(config['bgm']['win'])
        bgm['die'] = pg.mixer.Sound(config['bgm']['die'])
    except Exception as e:
        print(f"Warning: Failed to load BGM - {e}")
    return bgm

def play_bgm(bgm, bgm_type, volume=0.5):
    """Play background music of specified type"""
    channel = pg.mixer.Channel(BGM_CHANNEL)
    if bgm_type in bgm and not channel.get_busy():
        channel.set_volume(volume)
        channel.play(bgm[bgm_type], -1)

def stop_bgm():
    """Stop currently playing background music"""
    pg.mixer.Channel(BGM_CHANNEL).stop()


def main():
    """Main game loop and initialization"""
    config = load_config()
    bgm = init_audio(config)
    pg.init()
    try:
        icon = pg.image.load("assets/ui/window_icon.png")
        pg.display.set_icon(icon)
    except:
        print("Warning: Could not load window icon")
    screen = pg.display.set_mode((config["game"]["screen_width"], config["game"]["screen_height"]))
    pg.display.set_caption("Tomb Raider: Maze Adventure")
    game_manager = GameManager(config)
    gui_manager = GUIManager(config)
    current_totals = game_manager.get_current_enemy_totals()
    gui_manager.enemy_counts = {t: current_totals.get(t, 0) for t in gui_manager.enemy_types}

    def setup_gui_callbacks():
        """Set up callback functions for GUI interactions"""
        def _game():
            stop_bgm()
            play_bgm(bgm, 'game')
            gui_manager.current_screen = "game"
            game_manager.enemy_manager.activate_room(game_manager.player.current_room)
        
        def quit_game():
            stop_bgm()
            pg.quit()
            sys.exit()
        
        def _open_settings():
            stop_bgm()
            play_bgm(bgm, 'settings')
            gui_manager.previous_screen = gui_manager.current_screen
            gui_manager.current_screen = "settings"
            gui_manager.show_settings_buttons()
        
        def _open_settings_from_end():
            _open_settings()
        
        def restart_game():
            stop_bgm()
            play_bgm(bgm, 'game')
            game_manager.restart_game()
            gui_manager.victory = False
            gui_manager.current_screen = "game"
            current_totals = game_manager.get_current_enemy_totals()
            gui_manager.enemy_counts.update(current_totals)

        def apply_settings(counts):
            prev_screen = gui_manager.previous_screen
            stop_bgm()
            if prev_screen == "start":
                play_bgm(bgm, 'start')
            elif prev_screen == "game":
                play_bgm(bgm, 'game')
            elif prev_screen == "end":
                if gui_manager.victory:
                    play_bgm(bgm, 'win')
                else:
                    play_bgm(bgm, 'die')
            game_manager.randomize_enemies(counts)
            current_totals = game_manager.get_current_enemy_totals()
            gui_manager.enemy_counts.update(current_totals)
                
        gui_manager.settings_callback = apply_settings
        gui_manager.show_start_buttons(start_action=_game, quit_action=quit_game, settings_action=_open_settings)
        
        def on_screen_change(screen):
            stop_bgm()
            if screen == "start":
                play_bgm(bgm, 'start')
            elif screen == "game":
                play_bgm(bgm, 'game')
            elif screen == "end":
                if gui_manager.victory:
                    play_bgm(bgm, 'win')
                else:
                    play_bgm(bgm, 'die')
        
        gui_manager.on_screen_change_callback = on_screen_change
        
        return restart_game, quit_game, _open_settings_from_end

    restart_game, quit_game, open_settings_from_end = setup_gui_callbacks()
    clock = pg.time.Clock()
    running = True
    play_bgm(bgm, 'start')

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN and gui_manager.current_screen == "game":
                if event.key == pg.K_SPACE:
                    game_manager.player.shoot()
            gui_manager.handle_events(event)
            game_manager.minimap.handle_events(event)

        if gui_manager.current_screen == "game":
            game_manager.update()
            if game_manager.check_chest_and_exit(gui_manager, restart_game, quit_game, open_settings_from_end):
                stop_bgm()
                play_bgm(bgm, 'win')
                continue
            if game_manager.is_player_dead():
                game_manager.show_tip("You Died!", 1)
                draw_game_frame(screen, game_manager, gui_manager)
                pg.display.flip()
                pg.time.wait(1000)
                stop_bgm()
                play_bgm(bgm, 'die')
                gui_manager.victory = False
                gui_manager.show_end_buttons(
                    restart_action=restart_game,
                    quit_action=quit_game,
                    settings_action=open_settings_from_end
                )
                gui_manager.current_screen = "end"
                continue

        draw_current_screen(screen, game_manager, gui_manager)
        pg.display.flip()
        clock.tick(60)
    
    stop_bgm()
    game_manager.item_manager.save_state()
    pg.quit()

def draw_game_frame(screen, game_manager, gui_manager):
    """Draw the game frame including player, enemies, and GUI elements"""
    gui_manager.draw(
        screen, 
        game_manager.player, 
        game_manager.game_state,
        current_room_data=game_manager.get_current_room(),
        minimap=game_manager.minimap,
        room_neighbors=game_manager.room_neighbors,
        room_minimap_pos=game_manager.room_minimap_pos,
        rooms_config=game_manager.rooms_config,
        item_manager=game_manager.item_manager,
        enemy_manager=game_manager.enemy_manager
    )

def draw_current_screen(screen, game_manager, gui_manager):
    """Draw the appropriate screen based on current game state"""
    if gui_manager.current_screen == "game":
        draw_game_frame(screen, game_manager, gui_manager)
    else:
        gui_manager.draw(screen)

if __name__ == "__main__":
    main()