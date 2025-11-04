import pygame as pg
from typing import Dict, List, Tuple

class GUIManager:
    def __init__(self, config: Dict):
        # 加载配置（颜色、字体、尺寸）
        self.config = config
        self.colors = config["ui"]["colors"]  # 从ui节点获取颜色配置
        self.fonts = {
            "main": pg.font.Font(None, config["ui"]["fonts"]["main_font_size"]),  # 主字体
            "label": pg.font.Font(None, config["ui"]["fonts"]["label_font_size"]),  # 标签字体
            "title": pg.font.Font(None, 64)  # 标题字体（固定大小）
        }
        
        # 关键修改：从game节点获取屏幕尺寸（适配你的配置文件结构）
        self.screen_width = config["game"]["screen_width"]  # 原错误：config["screen_width"]
        self.screen_height = config["game"]["screen_height"]  # 原错误：config["screen_height"]
        
        # 界面状态（开始/游戏/结束）
        self.current_screen = "start"  # start / game / end
        self.buttons = []  # 存储按钮信息（每个按钮包含位置、文字、点击事件等）
        self.victory = False  # 用于结束界面区分"胜利"或"失败"状态

        # 添加纹理和图标
        try:
            self.icons = {
                "health": pg.image.load("assets/ui/heart_icon.png").convert_alpha(),
                "treasure": pg.image.load("assets/ui/treasure_icon.png").convert_alpha(),
            }
            # 缩放图标到合适尺寸
            for key in self.icons:
                self.icons[key] = pg.transform.scale(self.icons[key], (20, 20))
        except:
            self.icons = {}  # 备用，没有图片时也能运行

    def create_button(self, x: int, y: int, width: int, height: int, text: str, action, screen_name) -> None:
        """创建交互按钮"""
        self.buttons.append({
            "rect": pg.Rect(x, y, width, height),
            "text": text,
            "action": action,
            "hover": False,
            "screen": screen_name
        })

    def handle_events(self, event: pg.event.Event) -> None:
        if self.current_screen in ["start", "end"]:
            mouse_pos = pg.mouse.get_pos()
            for btn in self.buttons:
                if btn["screen"] != self.current_screen:
                    continue  # 只处理当前界面的按钮

                # 检测悬停
                btn["hover"] = btn["rect"].collidepoint(mouse_pos)

                # 检测点击
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if btn["rect"].collidepoint(mouse_pos):
                        btn["action"]()

    def draw_start_screen(self, screen: pg.Surface) -> None:
        """绘制开始界面"""
        screen.fill(self.colors["DARK_BROWN"])
        # 标题
        title = self.fonts["title"].render("Tomb Raider: Maze Adventure", True, self.colors["GOLD"])
        screen.blit(title, (self.screen_width//2 - title.get_width()//2, 150))
        # 绘制按钮
        for btn in self.buttons:
            if btn.get("screen") == "start":
                color = self.colors["LIGHT_BROWN"] if btn["hover"] else self.colors["BROWN"]
                pg.draw.rect(screen, color, btn["rect"], border_radius=10)
                pg.draw.rect(screen, self.colors["BLACK"], btn["rect"], 2, border_radius=10)
                text_surf = self.fonts["label"].render(btn["text"], True, self.colors["WHITE"])
                screen.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))
        # 操作提示
        tips = ["Arrow keys to move | Space to shoot | H to use food", "Find the treasure and reach the exit to win"]
        for i, tip in enumerate(tips):
            text = self.fonts["label"].render(tip, True, self.colors["WHITE"])
            screen.blit(text, (self.screen_width//2 - text.get_width()//2, 500 + i*30))

    def draw_hud(self, screen: pg.Surface, player, game_state: Dict) -> None:
        """绘制游戏内HUD(生命值、状态等）"""
        # 安全检查
        if player is None or game_state is None:
            return
            
        # 1. 生命值条
        # 调整位置（y从20改为10，上移10像素），高度从3改为10（更粗）
        health_bg = pg.Rect(20, 10, 200, 8)
        pg.draw.rect(screen, self.colors["RED"], health_bg)

        # 安全访问 health_system
        if hasattr(player, 'health_system') and player.health_system is not None:
            health_percentage = player.health_system.current_health / player.health_system.max_health
            # 同步调整当前生命值条的位置和高度
            pg.draw.rect(screen, self.colors["GREEN"], 
                        (20, 10, 200 * health_percentage, 8))
            
            # 生命值文本（用更大的main字体，上移位置）
            health_text = self.fonts["main"].render(  # 改用更大的main字体
                f"HP: {player.health_system.current_health}/{player.health_system.max_health}", 
                True, self.colors["BLACK"])
            screen.blit(health_text, (230, 8))  # y从18改为8，与粗血条对齐
        else:
            # 备用显示（同样放大字体并上移）
            health_text = self.fonts["main"].render("Health:  ?/?", True, self.colors["BLACK"])
            screen.blit(health_text, (230, 0))  # 上移到更顶部


        # 2. 房间与物品信息
        room_text = self.fonts["label"].render(
            f"Room: {getattr(player, 'current_room', '?')}/20", True, self.colors["BLACK"])
        screen.blit(room_text, (20, 23))
        
        # 3. 宝藏状态
        treasure_text = "Treasure Found" if game_state.get("has_treasure", False) else "Treasure Not Found"
        treasure_color = self.colors["GOLD"] if game_state.get("has_treasure", False) else self.colors["RED"]
        # 使用更大的main字体（配置中main_font_size为24，label为16）
        screen.blit(self.fonts["main"].render(treasure_text, True, treasure_color), (480, 18))  # 微调y坐标使其垂直居中


        # 4. 临时提示
        if game_state.get("tip_timer", 0) > 0:
            tip_bg = pg.Rect(200, 300, 400, 50)
            pg.draw.rect(screen, self.colors["WHITE"], tip_bg)
            pg.draw.rect(screen, self.colors["BROWN"], tip_bg, 2)
            tip_text = self.fonts["main"].render(game_state.get("tip_text", ""), True, self.colors["BROWN"])
            screen.blit(tip_text, tip_text.get_rect(center=tip_bg.center))

        # 5. 装备状态显示
        equipment_y = 35
        if hasattr(player, 'equipment') and player.equipment:
            # 标题用亮黄色，更醒目
            equip_text = self.fonts["label"].render("Equipment:", True, self.colors["YELLOW"])
            screen.blit(equip_text, (20, equipment_y))
            
            # 装备项用白色，与背景对比更强
            for i, item in enumerate(player.equipment.items()):
                equip_item = self.fonts["label"].render(f"- {item[0]}: {item[1]}", True, self.colors["WHITE"])
                screen.blit(equip_item, (40, equipment_y + 25 + i*25))
        else:
            # 无装备提示也用亮黄色
            no_equip = self.fonts["label"].render("No Equipment", True, self.colors["YELLOW"])
            screen.blit(no_equip, (20, equipment_y))

    def draw_end_screen(self, screen: pg.Surface) -> None:
        """绘制结束界面"""
        screen.fill(self.colors["DARK_BROWN"])
        # 结果文本
        result = "Victory! Successfully escaped!" if self.victory else "Defeat! Try again!"
        result_color = self.colors["GOLD"] if self.victory else self.colors["RED"]
        result_text = self.fonts["title"].render(result, True, result_color)
        screen.blit(result_text, (self.screen_width//2 - result_text.get_width()//2, 150))
        # 按钮
        for btn in self.buttons:
            if btn.get("screen") == "end":
                color = self.colors["LIGHT_BROWN"] if btn["hover"] else self.colors["BROWN"]
                pg.draw.rect(screen, color, btn["rect"], border_radius=10)
                pg.draw.rect(screen, self.colors["BLACK"], btn["rect"], 2, border_radius=10)
                text_surf = self.fonts["label"].render(btn["text"], True, self.colors["WHITE"])
                screen.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))

    def draw(self, screen: pg.Surface, player=None, game_state=None) -> None:
        """根据当前界面状态绘制对应内容"""
        if self.current_screen == "start":
            self.draw_start_screen(screen)
        elif self.current_screen == "game":
            # 确保 player 和 game_state 不为 None
            if player is not None and game_state is not None:
                self.draw_hud(screen, player, game_state)
            else:
                # 如果为 None，绘制一个基本的游戏界面
                screen.fill(self.colors["WHITE"])
                warning_text = self.fonts["main"].render("Loading game...", True, self.colors["BLACK"])
                screen.blit(warning_text, (self.screen_width//2 - warning_text.get_width()//2, self.screen_height//2))
        elif self.current_screen == "end":
            self.draw_end_screen(screen)