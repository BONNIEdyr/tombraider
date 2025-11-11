import os
import pygame as pg

# Centralized, fault-tolerant audio helper.
# Usage: from src.audio import play_sound

_SOUND_FILES = {
    # effects are under assets/audio/ in this repo
    'fireball': 'assets/audio/fireball.mp3',
    'bulletshot': 'assets/audio/bulletshot.mp3',
    'ough': 'assets/audio/ough.mp3',
    'button': 'assets/audio/button.mp3',
    'enemy_hurt': 'assets/audio/enemy_hurt.mp3',
    'HP_up': 'assets/audio/HP_up.mp3',
    'treasure': 'assets/audio/treasure.mp3',
}

_sounds = {}
_loaded = False


def _load_sounds():
    global _loaded
    if _loaded:
        return
    _loaded = True

    # Only attempt to load if mixer is initialized
    try:
        if not pg.mixer.get_init():
            # mixer not initialized; skip loading (main.py initializes mixer earlier)
            return
    except Exception:
        return

    for key, path in _SOUND_FILES.items():
        try:
            if os.path.exists(path):
                _sounds[key] = pg.mixer.Sound(path)
            else:
                # try loading anyway to allow pygame resource paths like within archives
                _sounds[key] = pg.mixer.Sound(path)
        except Exception:
            # ignore missing/corrupt sound files
            _sounds[key] = None


def play_sound(name: str, volume: float = 1.0):
    """Play a short sound by name. Safe no-op if sound missing or mixer not ready.

    name: one of the keys in _SOUND_FILES
    volume: 0.0-1.0
    """
    try:
        if not _loaded:
            _load_sounds()
        snd = _sounds.get(name)
        if snd:
            try:
                snd.set_volume(max(0.0, min(1.0, volume)))
            except Exception:
                pass
            try:
                snd.play()
            except Exception:
                pass
    except Exception:
        # Everything should be non-fatal
        pass
