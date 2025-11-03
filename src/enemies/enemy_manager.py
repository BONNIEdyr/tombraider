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

        # all_enemies: room_id (int) -> Group
        self.all_enemies: Dict[int, pg.sprite.Group] = {}

        # active room id and group
        self.active_room_id: Optional[int] = None
        self.active_group: pg.sprite.Group = pg.sprite.Group()

        # Global projectiles group managed by the EnemyManager
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
        if self.active_room_id == room_id:
            return self.active_group

        # create group if missing
        if room_id not in self.all_enemies:
            # find room data in rooms_config
            room_data = next((r for r in self.rooms_config.get("rooms", []) if r.get("room_id") == room_id), None)
            self._ensure_room_group(room_id, room_data)

        self.active_room_id = room_id
        self.active_group = self.all_enemies.get(room_id, pg.sprite.Group())
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
            if isinstance(res, Fireball) or isinstance(res, pg.sprite.Sprite):
                self.projectiles.add(res)

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

    def clear_all(self) -> None:
        """Clear all enemy and projectile groups."""
        for gid, g in self.all_enemies.items():
            for e in g:
                e.kill()
        self.all_enemies.clear()
        for p in self.projectiles:
            p.kill()
        self.projectiles.empty()
