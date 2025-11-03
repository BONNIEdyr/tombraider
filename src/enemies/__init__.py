"""Enemies package exports.

Provide explicit symbols so IDEs / type checkers (Pylance) recognize
the public API of this package and don't mark the imported classes as
"unused" or unresolved.
"""

from .base_enemy import Enemy
from .slime import Slime
from .bat import Bat
from .wizard import Wizard
from .guard import Guard

# Public API for `from src.enemies import *` and to help linters/type
# checkers (Pylance) know which names are intended to be exported.
__all__ = ["Enemy", "Slime", "Bat", "Wizard", "Guard"]