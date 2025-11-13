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
    # This class manages enemies and projectiles across rooms.
    def __init__(self, rooms_config: Dict):
        # Initialize enemy manager with room configuration.
        self.rooms_config = rooms_config
        self.enemy_types = ["slime", "bat", "wizard", "guard"]
        self.all_enemies: Dict[int, pg.sprite.Group] = {}
        self.enemy_states: Dict[int, Dict] = {}
        self.room_projectiles: Dict[int, pg.sprite.Group] = {}
        self.active_room_id: Optional[int] = None
        self.active_group: pg.sprite.Group = pg.sprite.Group()
        self.projectiles: pg.sprite.Group = pg.sprite.Group()

    # This function pre-loads enemy groups for all rooms.
    def load_all_rooms(self) -> None:
        for room in self.rooms_config.get("rooms", []):
            room_id = room.get("room_id")
            if room_id is None:
                continue
            self._ensure_room_group(room_id, room)

    # This function activates a room by ID and returns its enemy group.
    def activate_room(self, room_id: int) -> pg.sprite.Group:
        room_id = int(room_id)
        if self.active_room_id is not None:
            self.save_enemy_states(self.active_room_id)
            if self.active_room_id in self.room_projectiles:
                for projectile in self.room_projectiles[self.active_room_id]:
                    projectile.kill()
                self.room_projectiles[self.active_room_id].empty()
        if self.active_room_id == room_id:
            return self.active_group
        if room_id not in self.all_enemies:
            room_data = next((r for r in self.rooms_config.get("rooms", []) if r.get("room_id") == room_id), None)
            self._ensure_room_group(room_id, room_data)
        if room_id not in self.room_projectiles:
            self.room_projectiles[room_id] = pg.sprite.Group()
        self.active_room_id = room_id
        self.active_group = self.all_enemies.get(room_id, pg.sprite.Group())
        self.projectiles = self.room_projectiles[room_id]
        self.restore_enemy_states(room_id)
        return self.active_group

    # This function ensures that a sprite group exists for the given room and populates it.
    def _ensure_room_group(self, room_id: int, room_data: Optional[Dict]) -> None:
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
        if room_id not in self.room_projectiles:
            self.room_projectiles[room_id] = pg.sprite.Group()

    # This function creates an enemy instance from configuration data.
    def _create_enemy_from_data(self, data: Dict):
        t_raw = data.get("type", "").lower()
        if not t_raw:
            return None
        EnemyClass = ENEMY_MAPPING.get(t_raw)
        if EnemyClass is None:
            print(f"EnemyManager: unknown enemy type '{data.get('type')}', skipping")
            return None
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

    # This function saves the current state of enemies in a room.
    def save_enemy_states(self, room_id: int):
        if room_id in self.all_enemies:
            enemy_data = {}
            for enemy in self.all_enemies[room_id]:
                enemy_info = {
                    'type': enemy.__class__.__name__.lower(),
                    'pos': [enemy.rect.x, enemy.rect.y],
                    'hp': getattr(enemy, 'hp', 1),
                    'max_hp': getattr(enemy, 'max_hp', 1),
                    'speed': getattr(enemy, 'speed', 1)
                }
                key = f"{enemy.rect.x}_{enemy.rect.y}"
                enemy_data[key] = enemy_info
            self.enemy_states[room_id] = enemy_data

    # This function restores enemy states for a given room.
    def restore_enemy_states(self, room_id: int):
        if room_id in self.enemy_states:
            saved_states = self.enemy_states[room_id]
            current_enemies = list(self.all_enemies[room_id].sprites())
            for enemy in current_enemies:
                key = f"{enemy.rect.x}_{enemy.rect.y}"
                if key in saved_states:
                    state = saved_states[key]
                    enemy.hp = state['hp']
                    enemy.max_hp = state['max_hp']
                    if enemy.hp <= 0 and state['hp'] > 0:
                        enemy.hp = state['hp']

    # This function updates active enemies and their projectiles.
    def update(self, player_sprite) -> None:
        self.projectiles.update()
        for enemy in list(self.active_group.sprites()):
            try:
                res = enemy.update(player_sprite)
            except TypeError:
                res = enemy.update()
            except Exception as e:
                print(f"EnemyManager: error updating enemy {enemy}: {e}")
                res = None
            if isinstance(res, Fireball) or (hasattr(res, 'rect') and isinstance(res, pg.sprite.Sprite)):
                self.projectiles.add(res)
                if self.active_room_id in self.room_projectiles:
                    self.room_projectiles[self.active_room_id].add(res)

    # This function draws all projectiles and enemies on the screen.
    def draw(self, screen: pg.Surface) -> None:
        self.projectiles.draw(screen)
        self.active_group.draw(screen)
        for e in self.active_group:
            try:
                if hasattr(e, 'draw_health_bar'):
                    e.draw_health_bar(screen)
            except Exception:
                pass

    # This function returns the currently active enemy group.
    def get_active_enemies(self) -> pg.sprite.Group:
        return self.active_group

    # This function returns the current projectile group.
    def get_projectiles(self) -> pg.sprite.Group:
        return self.projectiles

    # This function clears all enemies and projectiles from a specific room.
    def clear_room(self, room_id: int) -> None:
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

    # This function clears all enemies and projectiles from all rooms.
    def clear_all(self) -> None:
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

    # This function resets all enemies and related states across rooms.
    def reset_all_enemies(self):
        self.all_enemies.clear()
        self.projectiles.empty()
        self.room_projectiles.clear()
        self.enemy_states.clear()
        self.active_group = pg.sprite.Group()
        self.active_room_id = None
        self.load_all_rooms()
