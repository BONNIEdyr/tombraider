# 导入游戏开发核心模块：pygame负责画面渲染和交互，sys处理程序退出，json读取房间配置
import pygame as pg
import sys
import json


# ==============================================================================
# 模块1：基础配置模块（初始化游戏窗口、字体、颜色等固定参数，全局复用）
# 作用：统一管理游戏基础样式，避免参数分散，后续修改样式只需改此模块
# ==============================================================================
def init_base_config():
    # 初始化pygame库（必须执行，否则无法使用pygame功能）
    pg.init()

    # 1. 窗口配置（自定义参数：屏幕宽高、窗口标题）
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # 游戏主窗口尺寸（像素），可根据需求调整
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # 创建游戏窗口
    pg.display.set_caption("古墓迷宫")  # 窗口标题，可修改为自定义名称

    # 2. 字体配置（自定义参数：字体文件路径、字体大小）
    # 优先加载系统「微软雅黑」字体（显示中文更美观），若找不到则用pygame默认字体
    try:
        # 字体1：用于提示框（如“获得宝箱”），字号24（清晰可见）
        main_font = pg.font.Font("C:/Windows/Fonts/msyh.ttc", 24)
        # 字体2：用于场景标注（如“古墓入口”），字号16（不遮挡场景）
        label_font = pg.font.Font("C:/Windows/Fonts/msyh.ttc", 16)
    except FileNotFoundError:
        main_font = pg.font.Font(None, 24)  # 默认字体（无中文优化）
        label_font = pg.font.Font(None, 16)

    # 3. 颜色配置（自定义参数：RGB颜色值，全局统一颜色风格）
    # 键名对应功能，值为RGB三元组，后续修改颜色只需改此处
    COLOR = {
        "WHITE": (230, 230, 230),  # 主场景背景色（浅灰，不刺眼）
        "BROWN": (139, 69, 19),  # 墙壁颜色（棕色，贴合“古墓”主题）
        "GREEN": (0, 255, 0),  # 玩家/出口颜色（绿色，代表安全/目标）
        "YELLOW": (255, 200, 0),  # 未收集宝箱颜色（黄色，醒目易识别）
        "BLUE": (0, 0, 255),  # 已收集宝箱颜色（蓝色，区分状态）
        "GRAY": (100, 100, 100),  # 小地图背景色（深灰，与主场景区分）
        "RED": (255, 0, 0),  # 小地图玩家标记色（红色，突出当前位置）
        "BLACK": (0, 0, 0),  # 边框/文字色（黑色，清晰不模糊）
        "LIGHT_GRAY": (200, 200, 200),  # 小地图房间底色（浅灰，区分房间格子）
        "DARK_GRAY": (90, 90, 90),  # 备用色（暂未使用，预留扩展）
    }

    return SCREEN_WIDTH, SCREEN_HEIGHT, screen, main_font, label_font, COLOR


# ==============================================================================
# 模块2：全局状态初始化模块（管理玩家、游戏进度、小地图坐标等动态数据）
# 作用：统一初始化动态数据，避免全局变量分散定义，便于维护状态变化
# ==============================================================================
def init_global_state():
    # 1. 玩家状态（自定义数据结构：记录玩家核心属性，随游戏进程变化）
    # 初始值仅为占位，实际会从JSON读取初始位置、默认房间等
    player = {
        "pos": [0, 0],  # 玩家当前位置（中心点坐标，[x,y]）
        "radius": 15,  # 玩家半径（15像素，大小适中，不遮挡场景）
        "speed": 5,  # 玩家移动速度（5像素/帧，60帧=1秒，移动流畅）
        "current_room": 1,  # 当前所在房间ID（初始为1号房，与JSON配置一致）
        "just_switched": False  # 房间切换锁定标记（防止连续切换，提升体验）
    }

    # 2. 游戏进度状态（自定义数据结构：记录宝箱收集、提示框等临时状态）
    game_state = {
        "has_treasure": False,  # 是否收集到宝箱（初始未收集，通关必需条件）
        "tip_text": "",  # 当前提示内容（如“获得宝箱”，空字符串为无提示）
        "tip_timer": 0  # 提示框显示帧数（60帧=1秒，倒计时结束后隐藏提示）
    }

    # 3. 探索进度状态（自定义数据结构：记录已探索房间，用于小地图显示）
    explored_rooms = [1]  # 已探索房间ID列表（初始仅1号房，探索新房间后追加）

    # 4. 小地图核心数据（自定义数据结构：关键！记录房间在小地图的相对位置）
    # 设计逻辑：以1号房为原点(0,0)，新房间按「连接方向」计算相对坐标（如右移+20，上移-20）
    # 格式：{房间ID: (小地图相对X, 小地图相对Y)}，确保房间按实际连接排列
    room_minimap_pos = {1: (0, 0)}  # 1号房初始相对坐标（原点）

    return player, game_state, explored_rooms, room_minimap_pos


# ==============================================================================
# 模块3：小地图配置模块（管理小地图尺寸、位置等固定参数，独立于主场景）
# 作用：单独配置小地图样式，避免与主场景参数混淆，便于调整小地图显示效果
# ==============================================================================
def init_minimap_config(SCREEN_WIDTH):
    # 自定义小地图参数（基于150×150正方形外框、20×20房间无间距设计，适配需求）
    minimap = {
        "w": 150, "h": 150,  # 小地图外框尺寸（150×150正方形，大小适中不遮挡主场景）
        "x": SCREEN_WIDTH - 160,  # 小地图初始X坐标（右上角，右边缘距屏幕右10像素）
        "y": 10,  # 小地图初始Y坐标（右上角，上边缘距屏幕上10像素）
        "cell_size": 20,  # 小地图单个房间尺寸（20×20正方形，无间距，150可容纳7个）
        "is_dragging": False,  # 小地图拖动状态（False=未拖动，True=正在拖动）
        "drag_off_x": 0,  # 拖动偏移X（记录鼠标按下时与小地图左边缘的距离，防跳变）
        "drag_off_y": 0  # 拖动偏移Y（记录鼠标按下时与小地图上边缘的距离，防跳变）
    }
    return minimap


# ==============================================================================
# 模块4：工具函数模块（封装重复使用的核心逻辑，如碰撞检测、提示显示等）
# 作用：减少代码冗余，将独立功能抽成函数，便于修改和复用
# ==============================================================================
def get_player_rect(player):
    """
    工具函数1：获取玩家的碰撞矩形（用于检测与墙壁、宝箱、出口的碰撞）
    参数：player - 玩家状态字典（含pos、radius）
    返回：pygame.Rect对象（矩形左上角坐标+宽高，代表玩家碰撞范围）
    设计逻辑：玩家pos是中心点，需转换为矩形左上角坐标（x=中心X-半径，y=中心Y-半径）
    """
    return pg.Rect(
        player["pos"][0] - player["radius"],  # 矩形左上角X
        player["pos"][1] - player["radius"],  # 矩形左上角Y
        player["radius"] * 2,  # 矩形宽度（玩家直径）
        player["radius"] * 2  # 矩形高度（玩家直径）
    )


def show_tip(game_state, text, duration=2):
    """
    工具函数2：显示提示框（如“获得宝箱”“你赢了”）
    参数：
        game_state - 游戏进度状态字典（用于存储提示内容和倒计时）
        text - 提示文本内容（字符串）
        duration - 提示显示时长（默认2秒，可自定义）
    设计逻辑：将秒转换为帧数（60帧=1秒），倒计时结束后自动隐藏提示
    """
    game_state["tip_text"] = text
    game_state["tip_timer"] = duration * 60  # 60帧/秒，确保不同帧率下显示时长一致


def check_wall_collision(new_pos, player, current_room_data):
    """
    工具函数3：检测玩家新位置是否与墙壁碰撞（含缺口判断，缺口处不碰撞）
    参数：
        new_pos - 玩家新位置（[x,y]，中心点坐标）
        player - 玩家状态字典（含radius）
        current_room_data - 当前房间数据（从JSON读取，含walls墙壁、gaps缺口）
    返回：True=碰撞（不能移动），False=不碰撞（可以移动）
    设计逻辑：先生成玩家碰撞矩形，再遍历墙壁判断，若在缺口位置则跳过碰撞检测
    """
    # 1. 生成玩家新位置的碰撞矩形
    player_rect = pg.Rect(
        new_pos[0] - player["radius"],
        new_pos[1] - player["radius"],
        player["radius"] * 2,
        player["radius"] * 2
    )

    # 2. 遍历当前房间所有墙壁，逐个判断碰撞
    for wall in current_room_data["walls"]:
        # 墙壁数据格式（JSON定义）：[x, y, width, height]（x,y=墙壁左上角，宽高=墙壁尺寸）
        wall_rect = pg.Rect(wall[0], wall[1], wall[2], wall[3])
        in_gap = False  # 标记是否在缺口位置（缺口处允许穿过，不碰撞）

        # 3. 检查当前墙壁是否对应缺口（缺口参数从JSON读取，格式：[基准坐标, 范围1, 范围2]）
        for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
            g_base, g_min, g_max = gap_info  # 缺口基准坐标+范围（如右缺口：g_base=x，g_min/g_max=y范围）

            # 右侧缺口：墙壁左边缘X=缺口X，且玩家Y在缺口Y范围内（允许穿过）
            if gap_dir == "right" and wall_rect.x == g_base and g_min <= new_pos[1] <= g_max:
                in_gap = True
                break
            # 左侧缺口：墙壁右边缘X=缺口X（墙壁X+宽度），且玩家Y在缺口Y范围内（允许穿过）
            elif gap_dir == "left" and (wall_rect.x + wall_rect.width) == g_base and g_min <= new_pos[1] <= g_max:
                in_gap = True
                break
            # 顶部缺口：墙壁下边缘Y=缺口Y（墙壁Y+高度），且玩家X在缺口X范围内（允许穿过）
            elif gap_dir == "top" and (wall_rect.y + wall_rect.height) == g_base and g_min <= new_pos[0] <= g_max:
                in_gap = True
                break
            # 底部缺口：墙壁上边缘Y=缺口Y，且玩家X在缺口X范围内（允许穿过）
            elif gap_dir == "bottom" and wall_rect.y == g_base and g_min <= new_pos[0] <= g_max:
                in_gap = True
                break

        # 4. 若在缺口位置，跳过当前墙壁；否则判断矩形碰撞
        if in_gap:
            continue
        if player_rect.colliderect(wall_rect):
            return True  # 碰撞，返回True（不能移动）

    return False  # 所有墙壁均不碰撞，返回False（可以移动）


# ==============================================================================
# 模块5：核心逻辑模块（处理房间切换、宝箱收集、出口检测等关键游戏流程）
# 作用：实现游戏核心玩法，关联工具函数和全局状态，驱动游戏进程
# ==============================================================================
def handle_room_switch(player, current_room_data, room_neighbors, explored_rooms, room_minimap_pos, minimap):
    """
    核心逻辑1：处理房间切换（基于玩家位置和缺口方向，更新玩家位置和小地图坐标）
    参数：
        player - 玩家状态字典（含pos、current_room等）
        current_room_data - 当前房间数据（含gaps缺口）
        room_neighbors - 房间连接关系（从JSON读取，如1号房右连2号房）
        explored_rooms - 已探索房间列表（新增房间时追加）
        room_minimap_pos - 小地图房间坐标字典（关键！计算新房间小地图位置）
        minimap - 小地图配置（含cell_size房间尺寸）
    设计逻辑：
        1. 切换后锁定（防止连续切换）；
        2. 按缺口方向判断是否触发切换；
        3. 计算新房间的小地图相对坐标（基于当前房间位置+切换方向）；
        4. 更新玩家位置和探索进度。
    """
    # 1. 切换锁定：玩家刚切换房间后，需移动到房间中间（100<X<700且100<Y<500）才能再次切换
    if player["just_switched"]:
        if 100 < player["pos"][0] < 700 and 100 < player["pos"][1] < 500:
            player["just_switched"] = False  # 解锁切换
        return  # 未解锁时不执行后续逻辑

    # 2. 提取玩家当前关键参数（pos=中心点，radius=半径）
    px, py, pr = player["pos"][0], player["pos"][1], player["radius"]

    # 3. 遍历当前房间所有缺口，判断是否触发切换
    for gap_dir, gap_info in current_room_data.get("gaps", {}).items():
        g_base, g_min, g_max = gap_info  # 缺口基准坐标+范围
        # 从JSON读取目标房间ID（当前房间+缺口方向=目标房间，如1号房+右=2号房）
        target_room_id = room_neighbors.get(str(player["current_room"]), {}).get(gap_dir)

        if target_room_id is None:
            continue  # 无目标房间（无连接），跳过当前缺口

        # 4. 按缺口方向判断切换触发条件（玩家边缘超出边界且在缺口范围内）
        switch_triggered = False
        new_player_pos = [px, py]  # 切换后玩家在新房间的位置

        # 左侧缺口切换：玩家左边缘≤缺口X，且Y在缺口范围→进入目标房间右侧
        if gap_dir == "left" and px - pr <= g_base and g_min <= py <= g_max:
            new_player_pos[0] = SCREEN_WIDTH - 50 - pr  # 新X=屏幕右-墙壁宽(50)-半径（贴右墙）
            switch_triggered = True
        # 右侧缺口切换：玩家右边缘≥缺口X，且Y在缺口范围→进入目标房间左侧
        elif gap_dir == "right" and px + pr >= g_base and g_min <= py <= g_max:
            new_player_pos[0] = 50 + pr  # 新X=墙壁宽(50)+半径（贴左墙）
            switch_triggered = True
        # 顶部缺口切换：玩家上边缘≤缺口Y，且X在缺口范围→进入目标房间底部
        elif gap_dir == "top" and py - pr <= g_base and g_min <= px <= g_max:
            new_player_pos[1] = SCREEN_HEIGHT - 50 - pr  # 新Y=屏幕下-墙壁宽(50)-半径（贴下墙）
            switch_triggered = True
        # 底部缺口切换：玩家下边缘≥缺口Y，且X在缺口范围→进入目标房间顶部
        elif gap_dir == "bottom" and py + pr >= g_base and g_min <= px <= g_max:
            new_player_pos[1] = 50 + pr  # 新Y=墙壁宽(50)+半径（贴上墙）
            switch_triggered = True

        # 5. 若触发切换，更新玩家状态和小地图坐标
        if switch_triggered:
            # 更新玩家位置和当前房间
            player["pos"] = new_player_pos
            player["current_room"] = target_room_id
            player["just_switched"] = True  # 锁定切换

            # 6. 新房间探索：计算并记录其小地图相对坐标（关键！按实际连接排列）
            if target_room_id not in explored_rooms:
                explored_rooms.append(target_room_id)  # 追加到已探索列表
                # 获取切换前房间（当前房间-目标房间=切换前房间ID）的小地图坐标
                prev_room_id = player["current_room"] - target_room_id  # 临时计算，仅适用于相邻切换
                prev_room_x, prev_room_y = room_minimap_pos[prev_room_id]
                cell_size = minimap["cell_size"]  # 房间尺寸（20像素）

                # 按切换方向计算新房间的小地图相对坐标（基于切换前房间位置）
                if gap_dir == "left":
                    new_room_x = prev_room_x - cell_size  # 左移：X-20
                    new_room_y = prev_room_y
                elif gap_dir == "right":
                    new_room_x = prev_room_x + cell_size  # 右移：X+20
                    new_room_y = prev_room_y
                elif gap_dir == "top":
                    new_room_x = prev_room_x
                    new_room_y = prev_room_y - cell_size  # 上移：Y-20
                elif gap_dir == "bottom":
                    new_room_x = prev_room_x
                    new_room_y = prev_room_y + cell_size  # 下移：Y+20
                else:
                    new_room_x, new_room_y = prev_room_x, prev_room_y  # 异常情况默认位置

                # 记录新房间的小地图相对坐标（确保后续绘制时按实际连接排列）
                room_minimap_pos[target_room_id] = (new_room_x, new_room_y)
            return  # 切换完成，退出函数


def handle_chest_and_exit(player, current_room_data, game_state, config, screen, main_font, COLOR, draw_game):
    """
    核心逻辑2：处理宝箱收集和出口检测（收集宝箱后更新状态，到达出口且有宝箱则通关）
    参数：
        player - 玩家状态字典
        current_room_data - 当前房间数据（含chests宝箱、is_exit是否出口）
        game_state - 游戏进度状态字典（含has_treasure宝箱状态）
        config - 全局配置（含exit_detection出口区域参数）
        screen - 游戏窗口（用于手动绘制通关画面）
        main_font - 提示框字体（用于绘制通关提示）
        COLOR - 颜色字典（用于绘制提示框）
        draw_game - 绘制函数（用于手动刷新通关画面）
    设计逻辑：
        1. 宝箱检测：玩家碰撞未收集宝箱→标记已收集+更新状态+显示提示；
        2. 出口检测：仅出口房间有效，玩家进入出口区域→有宝箱则通关，无则提示。
    """
    player_rect = get_player_rect(player)  # 获取玩家碰撞矩形

    # 1. 宝箱收集检测
    for chest in current_room_data.get("chests", []):
        # 仅检测未收集的宝箱（chest["is_got"]=False）
        if not chest["is_got"]:
            # 宝箱碰撞矩形：以宝箱pos为中心，30×30像素（与玩家大小匹配，便于碰撞）
            chest_rect = pg.Rect(
                chest["pos"][0] - 15,  # 左上角X=中心X-15（30÷2）
                chest["pos"][1] - 15,  # 左上角Y=中心Y-15
                30, 30  # 宽高=30像素
            )
            # 玩家与宝箱碰撞→收集宝箱
            if player_rect.colliderect(chest_rect):
                chest["is_got"] = True  # 标记宝箱已收集
                game_state["has_treasure"] = True  # 更新全局宝箱状态（通关必需）
                show_tip(game_state, "获得宝箱！可以去出口了！", 3)  # 显示提示（3秒）

    # 2. 出口检测（仅当前房间是出口房间时生效，is_exit=True）
    if current_room_data.get("is_exit"):
        # 从JSON读取出口区域参数：x_min=出口左边界，y_min=出口上边界，y_max=出口下边界
        exit_area = config["exit_detection"]
        # 出口碰撞矩形：X从x_min到屏幕右，Y从y_min到y_max（右侧长条区域，符合JSON定义）
        exit_rect = pg.Rect(
            exit_area["x_min"],
            exit_area["y_min"],
            SCREEN_WIDTH - exit_area["x_min"],  # 出口宽度=屏幕宽-出口左边界
            exit_area["y_max"] - exit_area["y_min"]  # 出口高度=出口下边界-上边界
        )

        # 玩家进入出口区域
        if player_rect.colliderect(exit_rect):
            # 有宝箱→通关成功
            if game_state["has_treasure"]:
                show_tip(game_state, "你赢了！", 2)  # 显示通关提示（2秒）
                draw_game(screen, player, current_room_data, label_font, COLOR, minimap, room_neighbors,
                          room_minimap_pos)  # 手动绘制画面
                pg.display.flip()  # 强制刷新屏幕（确保提示显示）
                pg.time.wait(2000)  # 等待2秒（让玩家看清提示）
                pg.quit()  # 退出pygame
                sys.exit()  # 退出程序
            # 无宝箱→提示收集
            else:
                show_tip(game_state, "还未找到宝藏！", 2)  # 显示提示（2秒）


# ==============================================================================
# 模块6：绘制模块（负责所有画面渲染，如主场景、小地图、提示框等）
# 作用：将游戏状态可视化，关联所有视觉元素，确保画面正确显示
# ==============================================================================
def draw_minimap(screen, minimap, room_minimap_pos, room_neighbors, player, COLOR):
    """
    绘制子模块1：绘制小地图（按实际连接关系排列房间，核心自定义逻辑）
    参数：
        screen - 游戏窗口（绘制目标）
        minimap - 小地图配置（含外框尺寸、位置）
        room_minimap_pos - 小地图房间坐标字典（关键！房间位置数据）
        room_neighbors - 房间连接关系（用于绘制连接线条）
        player - 玩家状态字典（含current_room，标记当前位置）
        COLOR - 颜色字典（用于绘制小地图元素）
    设计逻辑：
        1. 绘制小地图外框；
        2. 计算房间整体偏移（确保所有已探索房间在小地图内居中）；
        3. 按相对坐标绘制房间格子；
        4. 按实际连接关系绘制房间间线条；
        5. 标记玩家当前房间位置（红色圆点）。
    """
    # 1. 绘制小地图外框（150×150正方形，深灰背景+黑色边框）
    minimap_rect = pg.Rect(minimap["x"], minimap["y"], minimap["w"], minimap["h"])
    pg.draw.rect(screen, COLOR["GRAY"], minimap_rect)  # 小地图背景
    pg.draw.rect(screen, COLOR["BLACK"], minimap_rect, 2)  # 小地图边框（2像素粗）

    # 2. 计算房间整体偏移（关键！确保所有已探索房间在小地图内居中）
    if not room_minimap_pos:
        return  # 无已探索房间，跳过绘制
    # 收集所有已探索房间的相对坐标（X和Y分别收集）
    all_room_x = [pos[0] for pos in room_minimap_pos.values()]
    all_room_y = [pos[1] for pos in room_minimap_pos.values()]
    # 计算已探索房间的整体范围（最小X、最大X、最小Y、最大Y）
    min_room_x = min(all_room_x)
    max_room_x = max(all_room_x)
    min_room_y = min(all_room_y)
    max_room_y = max(all_room_y)
    # 计算偏移量：让房间范围在小地图内居中（外框宽-房间范围宽）//2，Y同理
    offset_x = minimap["x"] + (minimap["w"] - (max_room_x - min_room_x + minimap["cell_size"])) // 2
    offset_y = minimap["y"] + (minimap["h"] - (max_room_y - min_room_y + minimap["cell_size"])) // 2

    # 3. 绘制已探索房间（按相对坐标+偏移量，确保居中且按实际连接排列）
    room_rects = {}  # 临时存储房间绘制矩形（用于后续绘制连接线条和玩家）
    for room_id, (rel_x, rel_y) in room_minimap_pos.items():
        # 计算房间绘制位置：相对坐标 + 偏移量（让房间居中）
        draw_x = offset_x + (rel_x - min_room_x)  # X=偏移X + 相对X与最小X的差值
        draw_y = offset_y + (rel_y - min_room_y)  # Y=偏移Y + 相对Y与最小Y的差值
        # 绘制20×20正方形房间格子（浅灰底色+黑色边框）
        room_rect = pg.Rect(draw_x, draw_y, minimap["cell_size"], minimap["cell_size"])
        pg.draw.rect(screen, COLOR["LIGHT_GRAY"], room_rect)
        pg.draw.rect(screen, COLOR["BLACK"], room_rect, 1)  # 1像素边框，区分房间
        room_rects[room_id] = room_rect  # 记录房间绘制矩形

    # 4. 绘制房间连接线条（按实际连接关系，确保线条对应房间位置）
    for curr_room_id, connections in room_neighbors.items():
        curr_room_id = int(curr_room_id)  # JSON中房间ID是字符串，转换为整数
        # 仅绘制已探索的房间（未探索房间不显示连接）
        if curr_room_id not in room_rects or curr_room_id not in room_minimap_pos:
            continue
        # 遍历当前房间的所有邻居（如1号房的邻居是{"right":2}）
        for dir, neighbor_id in connections.items():
            if neighbor_id not in room_rects or neighbor_id not in room_minimap_pos:
                continue  # 邻居未探索，不绘制线条
            # 获取当前房间和邻居房间的绘制矩形
            curr_rect = room_rects[curr_room_id]
            neighbor_rect = room_rects[neighbor_id]
            # 按方向绘制连接线条（连接两个房间的中心点，线条粗2像素）
            if dir == "right":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midright, neighbor_rect.midleft, 2)
            elif dir == "left":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midleft, neighbor_rect.midright, 2)
            elif dir == "top":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midtop, neighbor_rect.midbottom, 2)
            elif dir == "bottom":
                pg.draw.line(screen, COLOR["BLACK"], curr_rect.midbottom, neighbor_rect.midtop, 2)

    # 5. 绘制玩家当前位置（红色圆点，在当前房间格子正中间，3像素粗，醒目）
    if player["current_room"] in room_rects:
        player_center = room_rects[player["current_room"]].center  # 房间格子中心点
        pg.draw.circle(screen, COLOR["RED"], player_center, 3)


def handle_minimap_drag(event, minimap):
    """
    绘制子模块2：处理小地图拖动（支持鼠标拖动小地图，提升操作体验）
    参数：
        event - pygame事件（如鼠标按下、松开、移动）
        minimap - 小地图配置（含拖动状态、偏移量）
    设计逻辑：
        1. 鼠标按下：判断是否点击小地图→记录拖动状态和偏移量；
        2. 鼠标松开：取消拖动状态；
        3. 鼠标移动：若拖动中→更新小地图位置（防跳变），且限制在屏幕内。
    """
    # 1. 鼠标按下（左键）：判断是否点击小地图
    if event.type == pg.MOUSEBUTTONDOWN:
        # 小地图碰撞矩形：判断鼠标位置是否在小地图内
        minimap_rect = pg.Rect(minimap["x"], minimap["y"], minimap["w"], minimap["h"])
        if minimap_rect.collidepoint(event.pos):
            minimap["is_dragging"] = True  # 标记为正在拖动
            # 记录偏移量：鼠标按下位置 - 小地图左/上边缘（防止拖动时小地图跳变）
            minimap["drag_off_x"] = event.pos[0] - minimap["x"]
            minimap["drag_off_y"] = event.pos[1] - minimap["y"]
    # 2. 鼠标松开：取消拖动状态
    elif event.type == pg.MOUSEBUTTONUP:
        minimap["is_dragging"] = False
    # 3. 鼠标移动：若拖动中，更新小地图位置
    elif event.type == pg.MOUSEMOTION and minimap["is_dragging"]:
        # 新位置=鼠标当前位置 - 偏移量（确保小地图跟随鼠标，无跳变）
        new_minimap_x = event.pos[0] - minimap["drag_off_x"]
        new_minimap_y = event.pos[1] - minimap["drag_off_y"]
        # 限制小地图在屏幕内（不超出屏幕边界）
        new_minimap_x = max(0, min(new_minimap_x, SCREEN_WIDTH - minimap["w"]))
        new_minimap_y = max(0, min(new_minimap_y, SCREEN_HEIGHT - minimap["h"]))
        # 更新小地图位置
        minimap["x"] = new_minimap_x
        minimap["y"] = new_minimap_y


def draw_game(screen, player, current_room_data, label_font, COLOR, minimap, room_neighbors, room_minimap_pos):
    """
    绘制主函数：绘制整个游戏画面（主场景+小地图+提示框）
    参数：
        screen - 游戏窗口（绘制目标）
        player - 玩家状态字典（绘制玩家）
        current_room_data - 当前房间数据（绘制墙壁、宝箱、出口）
        label_font - 标注字体（绘制“古墓入口”）
        COLOR - 颜色字典（绘制所有元素颜色）
        minimap - 小地图配置（传递给小地图绘制函数）
        room_neighbors - 房间连接关系（传递给小地图绘制函数）
        room_minimap_pos - 小地图房间坐标字典（传递给小地图绘制函数）
    设计逻辑：按层级绘制（背景→墙壁→标注→宝箱→出口→玩家→小地图→提示框），避免遮挡。
    """
    # 1. 绘制主场景背景（浅灰色，覆盖上一帧画面）
    screen.fill(COLOR["WHITE"])

    # 2. 绘制当前房间墙壁（棕色，按JSON定义的walls数据绘制）
    for wall in current_room_data["walls"]:
        pg.draw.rect(screen, COLOR["BROWN"], (wall[0], wall[1], wall[2], wall[3]))

    # 3. 绘制1号房“古墓入口”标注（仅在1号房显示，提示玩家起点）
    if player["current_room"] == 1:
        entrance_text = label_font.render("古墓入口", True, COLOR["BLACK"])  # 生成文字表面
        screen.blit(entrance_text, (10, 250))  # 绘制文字（位置：左10像素，下250像素）

    # 4. 绘制宝箱（未收集=黄色，已收集=蓝色，按JSON定义的chests数据绘制）
    for chest in current_room_data.get("chests", []):
        chest_color = COLOR["BLUE"] if chest["is_got"] else COLOR["YELLOW"]
        pg.draw.circle(screen, chest_color, chest["pos"], 15)  # 15像素圆形宝箱

    # 5. 绘制出口区域边框（仅出口房间显示，绿色3像素边框，提示出口位置）
    if current_room_data.get("is_exit"):
        exit_area = config["exit_detection"]
        # 绘制出口边框（不填充，仅边框）
        pg.draw.rect(
            screen,
            COLOR["GREEN"],
            (exit_area["x_min"], exit_area["y_min"], SCREEN_WIDTH - exit_area["x_min"],
             exit_area["y_max"] - exit_area["y_min"]),
            3  # 3像素边框粗
        )
        # 绘制“出口”文字标注（出口区域内，绿色文字）
        exit_text = label_font.render("出口", True, COLOR["GREEN"])
        screen.blit(exit_text, (exit_area["x_min"] + 10, exit_area["y_min"] + 10))

    # 6. 绘制玩家（绿色圆形，中心点=player["pos"]，半径=player["radius"]）
    pg.draw.circle(screen, COLOR["GREEN"], player["pos"], player["radius"])

    # 7. 绘制小地图（调用小地图绘制函数）
    draw_minimap(screen, minimap, room_minimap_pos, room_neighbors, player, COLOR)

    # 8. 绘制提示框（若有提示且倒计时未结束，显示白色背景+棕色边框+棕色文字）
    if game_state["tip_timer"] > 0:
        # 生成提示文字表面
        tip_text = main_font.render(game_state["tip_text"], True, COLOR["BROWN"])
        # 提示文字矩形（居中显示）
        tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        # 提示框背景矩形（比文字大20像素宽、10像素高，更美观）
        tip_bg_rect = tip_rect.inflate(20, 10)
        # 绘制提示框背景（白色填充+棕色边框）
        pg.draw.rect(screen, COLOR["WHITE"], tip_bg_rect)
        pg.draw.rect(screen, COLOR["BROWN"], tip_bg_rect, 2)
        # 绘制提示文字
        screen.blit(tip_text, tip_rect)


# ==============================================================================
# 模块7：主循环模块（游戏入口，驱动所有模块协同工作，处理事件和帧率）
# 作用：作为游戏“心脏”，循环处理输入、更新状态、绘制画面，直到程序退出
# ==============================================================================
def main():
    # 1. 初始化各模块（基础配置、全局状态、小地图配置）
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen, main_font, label_font, COLOR
    SCREEN_WIDTH, SCREEN_HEIGHT, screen, main_font, label_font, COLOR = init_base_config()

    global player, game_state, explored_rooms, room_minimap_pos
    player, game_state, explored_rooms, room_minimap_pos = init_global_state()

    global minimap
    minimap = init_minimap_config(SCREEN_WIDTH)

    # 2. 加载JSON配置文件（房间数据、连接关系、玩家初始位置等）
    global config
    with open('rooms_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 3. 从JSON更新玩家初始位置（覆盖全局状态的占位值，与配置一致）
    player["pos"] = list(config["player_spawn"])  # JSON中player_spawn是[x,y]，如[100,300]

    # 4. 初始化帧率控制器（60帧/秒，确保游戏速度稳定，不随电脑性能变化）
    clock = pg.time.Clock()
    running = True  # 游戏运行标记（True=运行，False=退出）

    # 5. 主循环（游戏核心循环，每帧执行一次）
    while running:
        # 5.1 处理事件（鼠标、键盘、窗口关闭等）
        for event in pg.event.get():
            # 窗口关闭事件→退出游戏
            if event.type == pg.QUIT:
                running = False
            # 小地图拖动事件→调用拖动处理函数
            handle_minimap_drag(event, minimap)

        # 5.2 处理玩家输入（键盘WASD或方向键控制移动）
        keys = pg.key.get_pressed()  # 获取当前所有按下的键
        spd = player["speed"]  # 玩家移动速度（5像素/帧）
        px, py = player["pos"]  # 玩家当前位置
        new_pos = [px, py]  # 玩家新位置（初始为当前位置，按按键更新）

        # 按按键更新新位置（上下左右）
        if keys[pg.K_w] or keys[pg.K_UP]:
            new_pos[1] -= spd  # 上移：Y减少
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            new_pos[1] += spd  # 下移：Y增加
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            new_pos[0] -= spd  # 左移：X减少
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            new_pos[0] += spd  # 右移：X增加

        # 5.3 边界与碰撞检查（确保玩家不超出屏幕，且不撞墙）
        # 边界检查：新位置X在0~屏幕宽，Y在0~屏幕高（不超出屏幕）
        if 0 <= new_pos[0] <= SCREEN_WIDTH and 0 <= new_pos[1] <= SCREEN_HEIGHT:
            # 碰撞检查：新位置不撞墙→更新玩家位置
            current_room = next(r for r in config["rooms"] if r["room_id"] == player["current_room"])
            if not check_wall_collision(new_pos, player, current_room):
                player["pos"] = new_pos

        # 5.4 执行核心逻辑（房间切换、宝箱收集、出口检测）
        handle_room_switch(player, current_room, config["room_neighbors"], explored_rooms, room_minimap_pos, minimap)
        handle_chest_and_exit(player, current_room, game_state, config, screen, main_font, COLOR, draw_game)

        # 5.5 提示框倒计时（每帧减1，直到0）
        if game_state["tip_timer"] > 0:
            game_state["tip_timer"] -= 1

        # 5.6 绘制游戏画面（调用绘制主函数，渲染所有元素）
        draw_game(screen, player, current_room, label_font, COLOR, minimap, config["room_neighbors"], room_minimap_pos)

        # 5.7 刷新屏幕（将绘制的内容显示到窗口上）
        pg.display.flip()

        # 5.8 控制帧率（固定60帧/秒，确保游戏速度稳定）
        clock.tick(60)

    # 6. 退出游戏（主循环结束后，释放pygame资源）
    pg.quit()


# ==============================================================================
# 程序入口（仅当直接运行此文件时执行主函数，避免被导入时自动运行）
# ==============================================================================
if __name__ == "__main__":
    main()