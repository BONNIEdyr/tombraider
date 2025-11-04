# tombraider
这是一个使用 Python 和 Pygame 库开发的 2D 动作冒险游戏项目。
## 文件结构
```
.
├── assets
│   ├── enemies
│   │   ├── bat.png
│   │   ├── guard.png
│   │   ├── mummy.png
│   │   └── wizard.png
│   └── ui
│       └── start_bg.png
├── config
│   ├── game_config.json
│   └── rooms_config.json
├── main.py
├── README.md
├── src
│   ├── enemies
│   │   ├── base_enemy.py
│   │   ├── bat.py
│   │   ├── enemy_manager.py
│   │   ├── guard.py
│   │   ├── __init__.py
│   │   ├── projectiles
│   │   │   ├── fireball.py
│   │   │   └── __init__.py
│   │   ├── slime.py
│   │   └── wizard.py
│   ├── gui
│   │   ├── gui_manager.py
│   │   └── minimap.py
│   └── player
│       ├── bullet.py
│       ├── constants.py
│       ├── health_system.py
│       ├── __init__.py
│       └── player.py
└── test_player.py


```
（每更新完代码可以在根目录的命令行里运行命令“tree"得到新的项目结构目录并更新）
### 进度
地图部分

制作了20个房间的地图，每个房间占满800\*600的窗口，走到缺口处刷新下一个房间

地图包含一个入口，一个出口，一个宝箱

我为了检验地图的可行性做了一个简单的玩家控制和显示ui，可以增改

现在代码大致可以实现玩家从初始房间入口出生，然后可以控制玩家移动到其他房间

没找到房间去出口会提示还没找到宝藏，找到宝藏再去出口会提示你赢了

地图json文件里有初始位置，出口位置，墙壁信息，房间连接，宝箱位置信息（其他陷阱位置信息什么的没写）







