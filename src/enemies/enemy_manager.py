import pygame as pg
from typing import Dict, Optional

from .slime import Slime
from .bat import Bat
from .wizard import Wizard
from .guard import Guard
from .projectiles.fireball import Fireball


ENEMY_MAPPING = {
    "slime": Slime,
    "bat": Bat,
    "wizard": Wizard,
    "guard": Guard,
}


class EnemyManager:
    """Manage enemies and projectiles across rooms.

    Responsibilities:
    - Initialize enemies from rooms configuration (supports both `pos` or `x`/`y`).
    - Keep per-room enemy groups so enemies persist across switches.
    - Update enemies each frame and collect projectiles produced by enemies (e.g. Wizard).
    - Provide draw/update helpers so `main.py` can delegate enemy logic to this manager.

    Usage (example):
        mgr = EnemyManager(rooms_config)
        mgr.load_all_rooms()
        mgr.activate_room(player['current_room'])

        # in game loop
        mgr.update(player_sprite)
        mgr.draw(screen)

    """

    def __init__(self, rooms_config: Dict):
        self.rooms_config = rooms_config
        self.enemy_types = ["slime", "bat", "wizard", "guard"]

        # all_enemies: room_id (int) -> Group
        self.all_enemies: Dict[int, pg.sprite.Group] = {}

        # 添加敌人状态保存
        self.enemy_states: Dict[int, Dict] = {}  # room_id -> enemy_data
        
        # 按房间管理火球
        self.room_projectiles: Dict[int, pg.sprite.Group] = {}  # room_id -> projectiles group

        # active room id and group
        self.active_room_id: Optional[int] = None
        self.active_group: pg.sprite.Group = pg.sprite.Group()

        # Global projectiles group (用于绘制和更新)
        self.projectiles: pg.sprite.Group = pg.sprite.Group()

    # --- Loading / initialization ---
    def load_all_rooms(self) -> None:
        """Pre-load enemy groups for all rooms defined in rooms_config."""
        for room in self.rooms_config.get("rooms", []):
            room_id = room.get("room_id")
            if room_id is None:
                continue
            self._ensure_room_group(room_id, room)

    def activate_room(self, room_id: int) -> pg.sprite.Group:
        """Activate (switch to) a room by id and return its enemy group."""
        room_id = int(room_id)
        
        # 保存当前活动房间的状态
        if self.active_room_id is not None:
            self.save_enemy_states(self.active_room_id)
            # 保存当前房间的火球
            if self.active_room_id in self.room_projectiles:
                # 清空当前房间的火球组
                for projectile in self.room_projectiles[self.active_room_id]:
                    projectile.kill()
                self.room_projectiles[self.active_room_id].empty()

        # 切换到新房间
        if self.active_room_id == room_id:
            return self.active_group

        # create group if missing
        if room_id not in self.all_enemies:
            # find room data in rooms_config
            room_data = next((r for r in self.rooms_config.get("rooms", []) if r.get("room_id") == room_id), None)
            self._ensure_room_group(room_id, room_data)

        # 确保房间有火球组
        if room_id not in self.room_projectiles:
            self.room_projectiles[room_id] = pg.sprite.Group()

        self.active_room_id = room_id
        self.active_group = self.all_enemies.get(room_id, pg.sprite.Group())
        
        # 切换到新房间的火球
        self.projectiles = self.room_projectiles[room_id]
        
        # 恢复新房间的敌人状态
        self.restore_enemy_states(room_id)
        
        return self.active_group

    def _ensure_room_group(self, room_id: int, room_data: Optional[Dict]) -> None:
        """Ensure that a pg.sprite.Group exists for the given room_id and populate it.

        room_data may be None (in which case an empty group is created).
        """
        room_id = int(room_id)
        if room_id in self.all_enemies:
            return

        group = pg.sprite.Group()
        if room_data and room_data.get("enemies"):
            for enemy_data in room_data.get("enemies", []):
                e = self._create_enemy_from_data(enemy_data)
                if e:
                    group.add(e)

        self.all_enemies[room_id] = group
        
        # 确保房间有火球组
        if room_id not in self.room_projectiles:
            self.room_projectiles[room_id] = pg.sprite.Group()

    def _create_enemy_from_data(self, data: Dict):
        """Create an enemy instance from config dict. Returns the instance or None on error."""
        t_raw = data.get("type", "").lower()
        if not t_raw:
            return None

        EnemyClass = ENEMY_MAPPING.get(t_raw)
        if EnemyClass is None:
            # unknown type
            print(f"EnemyManager: unknown enemy type '{data.get('type')}', skipping")
            return None

        # position support: 'pos': [x,y] or 'x'/'y'
        if "pos" in data and isinstance(data["pos"], (list, tuple)) and len(data["pos"]) >= 2:
            x, y = data["pos"][0], data["pos"][1]
        else:
            x, y = data.get("x"), data.get("y")

        if x is None or y is None:
            print(f"EnemyManager: skipping enemy with missing pos: {data}")
            return None

        try:
            return EnemyClass(x, y)
        except Exception as e:
            print(f"EnemyManager: error creating enemy {data}: {e}")
            return None

    # --- Enemy state management ---
    def save_enemy_states(self, room_id: int):
        """保存当前房间的敌人状态"""
        if room_id in self.all_enemies:
            enemy_data = {}
            for enemy in self.all_enemies[room_id]:
                # 保存敌人的关键状态信息
                enemy_info = {
                    'type': enemy.__class__.__name__.lower(),
                    'pos': [enemy.rect.x, enemy.rect.y],
                    'hp': getattr(enemy, 'hp', 1),
                    'max_hp': getattr(enemy, 'max_hp', 1),
                    'speed': getattr(enemy, 'speed', 1)
                }
                # 使用敌人位置作为唯一标识（简单方案）
                key = f"{enemy.rect.x}_{enemy.rect.y}"
                enemy_data[key] = enemy_info
            self.enemy_states[room_id] = enemy_data

    def restore_enemy_states(self, room_id: int):
        """恢复房间的敌人状态"""
        if room_id in self.enemy_states:
            saved_states = self.enemy_states[room_id]
            current_enemies = list(self.all_enemies[room_id].sprites())
            
            # 根据保存的状态恢复敌人属性
            for enemy in current_enemies:
                key = f"{enemy.rect.x}_{enemy.rect.y}"
                if key in saved_states:
                    state = saved_states[key]
                    enemy.hp = state['hp']
                    enemy.max_hp = state['max_hp']
                    # 如果敌人死亡但状态显示存活，需要重新激活
                    if enemy.hp <= 0 and state['hp'] > 0:
                        enemy.hp = state['hp']

    # --- Runtime: update / draw ---
    def update(self, player_sprite) -> None:
        """Update active enemies and projectiles.

        player_sprite: lightweight object exposing .rect required by enemy.update
        """
        # Update projectiles first (they may move independently)
        self.projectiles.update()

        # Iterate enemies and call their update; collect returned projectiles
        for enemy in list(self.active_group.sprites()):
            try:
                res = enemy.update(player_sprite)
            except TypeError:
                # Some enemy.update implementations may expect no args.
                res = enemy.update()
            except Exception as e:
                print(f"EnemyManager: error updating enemy {enemy}: {e}")
                res = None

            # If enemy produced a projectile (Wizard returns Fireball), add it
            if isinstance(res, Fireball) or (hasattr(res, 'rect') and isinstance(res, pg.sprite.Sprite)):
                self.projectiles.add(res)
                # 同时保存到房间特定的火球组
                if self.active_room_id in self.room_projectiles:
                    self.room_projectiles[self.active_room_id].add(res)

    def draw(self, screen: pg.Surface) -> None:
        """Draw projectiles then enemies (so projectiles appear above/below as desired)."""
        # Draw projectiles first so they render behind enemies, adjust order as needed
        self.projectiles.draw(screen)
        self.active_group.draw(screen)
        # draw health bars for enemies
        for e in self.active_group:
            try:
                if hasattr(e, 'draw_health_bar'):
                    e.draw_health_bar(screen)
            except Exception:
                pass

    # --- Utilities ---
    def get_active_enemies(self) -> pg.sprite.Group:
        return self.active_group

    def get_projectiles(self) -> pg.sprite.Group:
        return self.projectiles

    def clear_room(self, room_id: int) -> None:
        """Clear and remove stored enemies for a specific room."""
        if room_id in self.all_enemies:
            for e in self.all_enemies[room_id]:
                e.kill()
            del self.all_enemies[room_id]
        
        if room_id in self.room_projectiles:
            for p in self.room_projectiles[room_id]:
                p.kill()
            del self.room_projectiles[room_id]
            
        if room_id in self.enemy_states:
            del self.enemy_states[room_id]

    def clear_all(self) -> None:
        """Clear all enemy and projectile groups."""
        for gid, g in self.all_enemies.items():
            for e in g:
                e.kill()
        self.all_enemies.clear()
        
        for room_id, proj_group in self.room_projectiles.items():
            for p in proj_group:
                p.kill()
        self.room_projectiles.clear()
        
        self.enemy_states.clear()
        
        for p in self.projectiles:
            p.kill()
        self.projectiles.empty()