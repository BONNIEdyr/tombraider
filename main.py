import pygame as pg
import sys
import json
from src.game_manager import GameManager
from src.gui.gui_manager import GUIManager

def load_config():
    with open('config/game_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    config = load_config()
    
    # 初始化Pygame
    pg.init()
    
    # 设置窗口图标
    try:
        icon = pg.image.load("assets/ui/window_icon.png")
        pg.display.set_icon(icon)
    except:
        print("Warning: Could not load window icon")
    
    # 初始化屏幕
    screen = pg.display.set_mode((config["game"]["screen_width"], config["game"]["screen_height"]))
    pg.display.set_caption("古墓丽影：迷宫探险")

    # 初始化管理器
    game_manager = GameManager(config)
    gui_manager = GUIManager(config)

    # 设置回调函数
    def setup_gui_callbacks():
        def _game():
            gui_manager.current_screen = "game"
            game_manager.enemy_manager.activate_room(game_manager.player.current_room)
        
        def quit_game():
            pg.quit()
            sys.exit()
        
        def _open_settings():
            # 统计敌人总数
            totals = {t: 0 for t in gui_manager.enemy_types}
            for room in game_manager.rooms_config.get("rooms", []):
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
        
        def restart_game():
            game_manager.restart_game()
            gui_manager.victory = False
            gui_manager.current_screen = "game"

        # 设置回调
        def apply_settings(counts):
            # 这里实现设置应用逻辑（暂时留空）
            pass
            
        gui_manager.settings_callback = apply_settings
        gui_manager.show_start_buttons(start_action=_game, quit_action=quit_game, settings_action=_open_settings)
        
        return restart_game, quit_game, _open_settings_from_end

    restart_game, quit_game, open_settings_from_end = setup_gui_callbacks()

    # 主循环
    clock = pg.time.Clock()
    running = True

    while running:
        # 事件处理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            
            if event.type == pg.KEYDOWN and gui_manager.current_screen == "game":
                if event.key == pg.K_SPACE:
                    game_manager.player.shoot()
            
            # GUI事件处理
            gui_manager.handle_events(event)
            # 小地图事件处理
            game_manager.minimap.handle_events(event)

        # 根据当前界面状态更新
        if gui_manager.current_screen == "game":
            game_manager.update()
            
            # 检查胜利条件
            if game_manager.check_chest_and_exit(gui_manager, restart_game, quit_game, open_settings_from_end):
                continue
            
            # 检查游戏结束条件
            if game_manager.is_player_dead():
                game_manager.show_tip("You Died!", 1)
                # 绘制最后画面
                draw_game_frame(screen, game_manager, gui_manager)
                pg.display.flip()
                pg.time.wait(1000)
                
                gui_manager.victory = False
                gui_manager.show_end_buttons(
                    restart_action=restart_game,
                    quit_action=quit_game,
                    settings_action=open_settings_from_end
                )
                gui_manager.current_screen = "end"
                continue

        # 绘制
        draw_current_screen(screen, game_manager, gui_manager)
        
        pg.display.flip()
        clock.tick(60)
    
    # 退出前保存
    game_manager.item_manager.save_state()
    pg.quit()

def draw_game_frame(screen, game_manager, gui_manager):
    """绘制游戏帧"""
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
    """根据当前界面状态绘制"""
    if gui_manager.current_screen == "game":
        draw_game_frame(screen, game_manager, gui_manager)
    else:
        gui_manager.draw(screen)

if __name__ == "__main__":
    main()