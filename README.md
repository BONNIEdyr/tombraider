# Tomb Raider: Maze Adventure

A 2D action-adventure game developed with Python and Pygame. Players will explore rooms, combat enemies, collect treasures, and ultimately find the exit to complete their adventure in an ancient tomb maze.

## Project Overview

This project is a Tomb Raider-like maze exploration game. Core gameplay includes room exploration, enemy combat, item collection, and treasure hunting. The game features a modular design, encompassing player systems, enemy systems, map systems, item systems, and GUI interaction systems. It supports scene switching, progress tracking, and simple combat mechanics.

## Core Features

- **Maze Exploration:** Features 20 unique rooms, each 800x600 pixels, connected via gaps to enable scene transitions.
- **Player System:** Supports movement, shooting (Spacebar), health management, and collecting items to enhance abilities.
- **Enemy System:** Multiple enemy types (Slime, Bat, Wizard, Guard), with the Wizard capable of firing fireballs.
- **Item System:** Includes restorative items (First-Aid Kit restores 50% health, Food restores 20% health) and traps (e.g., falling rocks).
- **Objective Mechanic:** Players must first find the treasure before reaching the exit to win. Reaching the exit without the treasure prompts them to continue exploring.
- **Interface Interaction:** Includes a start screen, in-game interface (with minimap), and end screen. Supports configuration like adjusting enemy count.

## File Structure

```
.
├── assets/           # Game assets
│   ├── enemies/      # Enemy sprites
│   ├── items/        # Item sprites
│   └── ui/           # UI backgrounds, icons, etc.
├── config/           # Configuration files
│   ├── game_config.json   # Global game configuration (screen size, colors, etc.)
│   ├── rooms_config.json  # Room configurations (walls, enemies, treasure positions, etc.)
│   └── items_state.json   # Item state saving
├── src/              # Source code
│   ├── enemies/      # Enemy-related classes (base class, specific enemies, projectiles)
│   ├── gui/          # Interface management (GUI, minimap)
│   ├── items/        # Item-related classes (consumables, traps)
│   └── player/       # Player-related classes (movement, shooting, health)
├── main.py           # Game main entry point
└── test_player.py    # Player-related tests
```

## Installation and Running

### Prerequisites
- Python 3.x
- Pygame library

### Installation and Execution
1. Install dependencies: `pip install pygame`
2. Run the game: `python main.py`

## Game Controls

- **Movement:** Arrow keys (↑↓←→) to control player movement.
- **Shooting:** Spacebar to fire bullets (to combat enemies).
- **Minimap:** Can be dragged to reposition. Displays explored rooms and current location.
- **Interface:** Click buttons to navigate screens (Start/Settings/Quit, etc.).

## Progress and Plans

### Implemented Features
- Map layout and switching logic for 20 rooms.
- Player movement, shooting, and health management.
- Spawning of multiple enemy types with basic AI (Wizard ranged attacks, enemy chasing, etc.).
- Treasure collection and exit victory condition.
- Basic GUI screens (Start/Game/End) and minimap.
- Item system (restorative items, traps).

### Planned Features
- More enemy types and behavioral patterns.
- Complex trap mechanisms (e.g., spikes, poison gas).
- Weapon upgrade system.
- Save and load functionality.
- Sound effect and music optimization.







