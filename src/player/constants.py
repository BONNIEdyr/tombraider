# 玩家常量配置
PLAYER_CONFIG = {
    "radius": 15,
    "speed": 5,
    "max_health": 100,
    "color": (0, 255, 0),  # 绿色玩家
    "invincible_duration": 60  # 无敌帧数（1秒）
}

# 子弹配置
BULLET_CONFIG = {
    "radius": 5,
    "speed": 8,
    "damage": 10,
    "color": (255, 255, 0),  # 黄色
    "max_bullets": 5,
    "cooldown": 15,
    "max_ammo": 30,  # 新增：最大子弹数量限制
    "initial_ammo": 10  # 新增：初始子弹数量
}
  

# 控制键位
CONTROLS = {
    'UP': ['w', 'up'],
    'DOWN': ['s', 'down'], 
    'LEFT': ['a', 'left'],
    'RIGHT': ['d', 'right'],
    'SHOOT': 'space'
}