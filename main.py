import pygame as pg
import sys
import json
import random  
from src.game_manager import GameManager
from src.gui.gui_manager import GUIManager

# 新增：BGM通道常量（Pygame默认有8个通道）
BGM_CHANNEL = 0  # 专用通道播放BGM，避免与其他音效冲突

def load_config():
    with open('config/game_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 新增：初始化音频并加载BGM
def init_audio(config):
    pg.mixer.init()
    # 加载所有BGM
    bgm = {}
    try:
        bgm['start'] = pg.mixer.Sound(config['bgm']['start'])
        bgm['settings'] = pg.mixer.Sound(config['bgm']['settings'])
        bgm['game'] = pg.mixer.Sound(config['bgm']['game'])
        bgm['win'] = pg.mixer.Sound(config['bgm']['win'])
        bgm['die'] = pg.mixer.Sound(config['bgm']['die'])
    except Exception as e:
        print(f"警告:加载BGM失败 - {e}")
    return bgm

# 新增：播放BGM的函数
def play_bgm(bgm, bgm_type, volume=0.5):
    channel = pg.mixer.Channel(BGM_CHANNEL)
    if bgm_type in bgm and not channel.get_busy():
        channel.set_volume(volume)
        channel.play(bgm[bgm_type], -1)  # -1表示无限循环

# 新增：停止当前BGM
def stop_bgm():
    pg.mixer.Channel(BGM_CHANNEL).stop()


def main():
    config = load_config()


    # 初始化音频和BGM（新增）
    bgm = init_audio(config)  # 加载所有BGM资源
    
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
    
    # 初始化敌人数量显示
    current_totals = game_manager.get_current_enemy_totals()
    gui_manager.enemy_counts = {t: current_totals.get(t, 0) for t in gui_manager.enemy_types}

    # 设置回调函数
    def setup_gui_callbacks():
        def _game():
            # 切换到游戏界面：停止当前BGM，播放游戏BGM（新增）
            stop_bgm()
            play_bgm(bgm, 'game')

            gui_manager.current_screen = "game"
            game_manager.enemy_manager.activate_room(game_manager.player.current_room)
        
        def quit_game():
            # 退出游戏：停止BGM（新增）
            stop_bgm()
            pg.quit()
            sys.exit()
        
        def _open_settings():
            # 打开设置界面：停止当前BGM，播放设置BGM（新增）
            stop_bgm()
            play_bgm(bgm, 'settings')

            # 统计敌人总数（现在直接从 enemy_counts 获取）
            gui_manager.previous_screen = gui_manager.current_screen
            gui_manager.current_screen = "settings"
            gui_manager.show_settings_buttons()
        
        def _open_settings_from_end():
            _open_settings()
        
        def restart_game():
            # 重启游戏：停止当前BGM，播放游戏BGM（新增）
            stop_bgm()
            play_bgm(bgm, 'game')

            game_manager.restart_game()
            gui_manager.victory = False
            gui_manager.current_screen = "game"
            
            # 重启后更新敌人数量显示
            current_totals = game_manager.get_current_enemy_totals()
            gui_manager.enemy_counts.update(current_totals)

        # 设置回调
        def apply_settings(counts):
            # 应用设置后返回之前的界面，恢复对应BGM（新增）
            prev_screen = gui_manager.previous_screen
            stop_bgm()  # 先停止当前BGM
            # 根据之前的界面恢复对应的BGM
            if prev_screen == "start":
                play_bgm(bgm, 'start')
            elif prev_screen == "game":
                play_bgm(bgm, 'game')
            elif prev_screen == "end":
                if gui_manager.victory:
                    play_bgm(bgm, 'win')  # 胜利界面BGM
                else:
                    play_bgm(bgm, 'die')  # 失败界面BGM

            # 调用 GameManager 的随机化敌人方法
            game_manager.randomize_enemies(counts)
            
            # 更新 GUI 显示的敌人数量
            current_totals = game_manager.get_current_enemy_totals()
            gui_manager.enemy_counts.update(current_totals)
                
        gui_manager.settings_callback = apply_settings
        gui_manager.show_start_buttons(start_action=_game, quit_action=quit_game, settings_action=_open_settings)
        
        # 新增：界面切换时的BGM回调
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

    # 主循环
    clock = pg.time.Clock()
    running = True

    # 初始界面为开始界面，播放start BGM（新增）
    play_bgm(bgm, 'start')

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
                # 胜利时：停止当前BGM，播放胜利BGM（新增）
                stop_bgm()
                play_bgm(bgm, 'win')
                continue
            
            # 检查游戏结束条件
            if game_manager.is_player_dead():
                game_manager.show_tip("You Died!", 1)
                # 绘制最后画面
                draw_game_frame(screen, game_manager, gui_manager)
                pg.display.flip()
                pg.time.wait(1000)

                # 死亡时：停止当前BGM，播放死亡BGM（新增）
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

        # 绘制
        draw_current_screen(screen, game_manager, gui_manager)
        
        pg.display.flip()
        clock.tick(60)
    
    # 退出前保存
    stop_bgm()
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