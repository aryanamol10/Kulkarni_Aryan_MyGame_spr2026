# Level Design Legend

This document explains what each character represents in the level `.txt` files located in the `Levels/` directory.

## Tile Key

| Character | Name | Description |
|-----------|------|-------------|
| `1` | **Wall** | Solid obstacle that blocks player and enemy movement. Appears as a dark gray tile. |
| `.` | **Floor** | Walkable empty space. Appears as a dark blue tile with grid lines. |
| `P` | **Player** | Player starting position. Only one per level. |
| `o` | **Coin** | Collectible item that increases score. Player gains points by walking over coins. |
| `T` | **Trap** | Damaging obstacle. Deals 10 damage to the player on contact. Appears as a red tile. |
| `E` | **Enemy** | Basic enemy (Type E). Fast melee enemy that pursues the player. |
| `A` | **Door A** | In `level_1.txt`: Opens path to Boss_1 room. In boss levels: Spawns Boss Type A enemy. |
| `B` | **Door B** | In `level_1.txt`: Opens path to Boss_2 room. In boss levels: Spawns Boss Type B enemy. |
| `C` | **Door C** | In `level_1.txt`: Opens path to Boss_3 room. In boss levels: Spawns Boss Type C enemy. |
| `D` | **Door D** | In `level_1.txt`: Opens path to Boss_4 room. In boss levels: Spawns Boss Type D enemy. |

---

## Enemy Types

### Type E (Basic Enemy)
- **Health:** 32 HP
- **Speed:** 140 units/sec
- **Behavior:** Melee; chases player directly
- **Threat:** Low damage but fast
- **Color:** Magenta

### Type A (Boss A)
- **Health:** 180 HP
- **Speed:** 90 units/sec
- **Behavior:** Melee; rushes player
- **Special:** None
- **Color:** Red

### Type B (Boss B)
- **Health:** 120 HP
- **Speed:** 60 units/sec
- **Behavior:** Ranged; shoots projectiles at player
- **Special:** Fires energy bullets
- **Color:** Blue

### Type C (Boss C)
- **Health:** 140 HP
- **Speed:** 80 units/sec
- **Behavior:** Ranged; moves in zigzag pattern while chasing
- **Special:** Unpredictable movement
- **Color:** Purple

### Type D (Boss D)
- **Health:** 260 HP
- **Speed:** 40 units/sec (slowest)
- **Behavior:** Stationary turret; fires constantly
- **Special:** Highest HP; stays in place
- **Color:** Gold

---

## Level Files

### `level_1.txt`
- **Purpose:** Hub/main level
- **Goal:** Navigate to one of the four doors (A, B, C, D) to enter a boss room
- **Tiles Used:** `1`, `.`, `P`, `o`, `T`, `E`, `A`, `B`, `C`, `D`

### `Boss_1.txt`, `Boss_2.txt`, `Boss_3.txt`, `Boss_4.txt`
- **Purpose:** Boss encounter rooms
- **Goal:** Defeat the spawned boss (Type A, B, C, or D respectively)
- **Tiles Used:** `1`, `.`, `P`, `o`, `T`, `E`, `A/B/C/D`
- **Special:** Boss type letters spawn a single boss enemy; regular `E` tiles spawn weak enemies

---

## Level Design Tips

- **Layout:** Rooms are surrounded by `1` (walls). Leave `.` (floor) for walkable areas.
- **Player Start:** Place `P` in a safe zone away from enemies.
- **Coins:** Distribute `o` throughout the level for points.
- **Difficulty:** Add more `E` or `T` for harder challenges.
- **Boss Fights:** Boss rooms typically have fewer obstacles and focus on the boss encounter.

---

## Example

```
11111111111111111
1.................1
1....11111.11111..1
1..o..o...A...o..o1
1.................1
1...E.....E.....E.1
1.............TT..1
1....o...........o1
1.......P.........1
1...o.....o....o..1
1.................1
11111111111111111
```

In this example:
- Border of `1` creates the room boundary
- `P` is the player spawn (center-bottom)
- `A` is the Boss A spawn point
- `E` tiles are scattered enemies
- `o` tiles are coins to collect
- `T` tiles are traps to avoid
- `.` tiles are safe walkable floor
