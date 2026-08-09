# 🎮 Game Design Document: RGBox
## 1. Core Concept
* **Genre:** Minimalist Puzzle-Platformer.
* **Core Loop:** The player controls a box that changes its size and gains new movement abilities by mixing primary colors (RGB) to overcome obstacles and solve puzzles.
* **Art Style & Atmosphere:** Minimalist, 8 fixed colors (3-bit RGB palette), solid black background.
* **Number of Levels (6):**
  * `0.0` — First Tutorial (Basic movement).
  * `0.1` — Second Tutorial (Color changing mechanics).
  * `1.0` — Level 1.
  * `1.1` — Level 2.
  * `1.2` — Level 3.
  * `1.3` — Level 4 (Final test).
## 2. Technical Specs
* **Engine:** Python / Pygame.
* **Base Unit Scale (UNIT):** 8.
* **Tile Size:** 64x64 px (8 * UNIT).
* **Window Resolution:** 960x768 px (15x12 tiles, 5:4 aspect ratio).
* **Camera:** Player-centered camera (drawing offset).
* **Controls:** Arrow Keys — Movement, Spacebar — Jump, (Key) — Dash, R — Restart Level.
## 3. Player States & Physics
* **Player Sizes:**
  * Tier 1 (Single color): `56x56 px` (Can fit through a 1-tile gap).
  * Tier 2 (Two colors mixed): `72x72 px`.
  * Tier 3 (White - all three colors mixed): `88x88 px`.
* **Movement Physics:** Strict separation of X and Y axis collisions. Implementation of Terminal Velocity (max fall speed) to prevent clipping.
* **Game Feel Mechanics:**
  * **Coyote Time:** Yes (The player can still jump for a split second after running off a ledge).
  * *Jump Buffer:* No (Saved for Project #2).
  * *Variable Jump Height:* No (Saved for Project #3).
  * *Squash & Stretch:* No.
## 4. Abilities & Mechanics
*Abilities are combined through additive color mixing.*
* **Red:** `Wall Jump`.
* **Green:** `Dash` (Quick horizontal burst).
* **Blue:** `Double Jump` (Mid-air jump).
* **Yellow (Red + Green):** Wall Jump + Dash.
* **Cyan (Green + Blue):** Dash + Double Jump.
* **Magenta (Red + Blue):** Wall Jump + Double Jump.
* **White (Red + Green + Blue):** Wall Jump + Dash + Double Jump (Final Form).
## 5. Map Elements & Tiled Layers
*Levels will be designed using the Tiled editor (.tmx format).*
* **Terrain:** Solid blocks (Walls, floor, ceiling). Blocks player movement.
* **Color Stations (Triggers):** Zones/pools in the level where the player absorbs or drains specific colors.
* **Hazards:** Red spikes or lasers. Touching them results in instant death and level restart.
* **Exit Door (Trigger):** The zone that transitions the player to the next level.
## 6. HUD / UI
* To be designed later in the development process.
## Color System (RGB) and Size Architecture
In **RGBox**, the mechanics of changing character color and size are the core of gameplay. To avoid physics errors and keep the code clean, the system is divided into three logical blocks: Data, Triggers, and Physics.
### 1. Color Storage and Mixing (Data)
The player's current color is stored in a video dictionary, which represents the unusual RGB color model:
``` Python
self.colors = {'R': 255, 'G': 0, 'B': 0} # Player starts: Red