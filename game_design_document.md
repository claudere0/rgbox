# 🎮 RGBox: Game Design Document (GDD)

**Stack:** Python 3.11, Pygame-CE, PyTMX, Tiled Editor, Aseprite (Graphics). Sound and music assets to be sourced.
**Genre:** Puzzle / Precision Platformer (inspired by Celeste and Thomas Was Alone, but smaller in scope).

## 📖 1. Core Concept
The player controls a cube that absorbs light pigments based on the RGB system (Red, Green, Blue).

*   **Black Cube (0 colors):** A small, basic cube with no abilities. Symbolizes emptiness.
*   **Colored Cube:** By absorbing colors at "Color Stations", the cube mixes them (Additive RGB mixing), grows in size, and gains unique abilities.
*   **World Inversion:** If the player is Black, the background is White and platforms are Black. When the player absorbs any color, the world instantly inverts (Background becomes Black, platforms become White), causing the colored player to glow brightly in the dark.
*   **Game Scope:** 6 dense, perfectly tuned levels with zero filler (2 tutorials, 4 main levels). Each level focuses on unique color combinations and "Color Doors" (Doors that only allow an empty cube or a cube of a matching color to pass).

### Level Progression Prototype (Draft)
*   **Tutorial 1 (Level 0-0):** Starts as a Black box. Teaches basic movement. In the middle of the map, the player receives Red and learns how to use the Dash ability. A portal leads to the next level.
*   **Tutorial 2 (Level 0-1):** Starts as Red (World is black). In the middle of the map, the player must drop the Red pigment to pass through "Black Doors". Finds a new Color Station with Green pigment, then navigates to the portal.
*   **Main Game (Level 1-0):** Starts as Green. In the first third of the map, the player drops Green to pass through Black doors and finds Blue. In the second third, the player navigates using Blue. In the final third, Green abilities are required, forcing the player to backtrack through Blue doors to retrieve Green, becoming Cyan (Green + Blue), and exiting through the portal.
*   *(Remaining 3 levels to be designed later).*

## 🛠 2. Implemented Features (Architecture & Mechanics)

### A. Finite State Machine (FSM)
Fully implemented clean FSM for the Player. `handle_input()` and `update(dt)` are strictly separated.
**Implemented States:** `IdleState`, `RunState`, `FallState`, `JumpState`, `WallSlideState`, `DashState`.

### B. Advanced Physics (Precision Platformer Physics)
Physics are mathematically calculated (1 unit = 8px, 1 meter = 64px, Gravity = 2560 px/s²).
*   **Axis-Separated Collisions:** X-axis movement -> X-axis collision, then Y-axis movement -> Y-axis collision. Prevents corner sticking.
*   **Terminal Velocity:** Maximum fall speed is capped at 1600 px/s to prevent falling through tiles.
*   **Dynamic Gravity:** Fall gravity is multiplied by 2 (for jump weight/heaviness), Wall Slide gravity is multiplied by 0.125.
*   **QoL Features:**
    *   **Coyote Time (125 ms):** Allows jumping shortly after running off a ledge.
    *   **Jump Buffer / Wall Jump Block (250 ms):** Blocks movement input briefly after a wall jump to preserve momentum.

### C. Size and Color Mechanics (Core Loop)
The player has a dictionary: `pigments = {'R': False, 'G': False, 'B': False}`.
*   **Dynamic Size:** Calculated via formula: `new_size = (5 + 2 * color_count) * 8`. (Black = 40px, 1 color = 56px, 2 colors = 72px, 3 colors = 88px).
*   **Safe Growth:** When changing size, a new `pygame.Rect` is created and strictly anchored by its `bottom` attribute to the previous location to prevent clipping into the floor. Additionally, color changes trigger a small upward jump impulse (Game Feel).

### D. Abilities Binding
Abilities are not hardcoded into states; they are granted only if the specific pigment is present:
*   🟥 **Red (R):** Unlocks **Dash**.
*   🟩 **Green (G):** Unlocks **Double Jump** (mid-air).
*   🟦 **Blue (B):** Unlocks **Wall Slide** and **Wall Jump**.

### E. Interactive Map and Stations (PyTMX)
*   The `terrain` layer is parsed into static tiles. If `has_colors == True`, textures for all tiles are swapped on the fly from black to white.
*   **ColorStation:** Interactive objects (Trigger Sprites). The player presses 'E' while standing on 1 of 3 station segments to absorb or deposit a pigment. Stations redraw themselves automatically based on the background inversion (black/white).

## 🚀 3. Roadmap (What's Next)

### Phase 1: Interactive Objects and Levels (In Progress)
Need to implement classes for the following Tiled `objects`:
*   **Spikes & Death:** Instant, seamless respawn (no loading screens) upon touching the `hazard_sprites` group.
*   **ColorDoor:** A solid block. Its `self.rect` only allows the Player to pass if the player is Black (for "empty" doors) or if the player's color exactly matches the door's color. Forces players to drop abilities at stations.
*   **Portal:** Level transition trigger. Clears the current level and parses the next `.tmx` file.
*   **JumpPads (Trampolines):** Propel the player upward along the Y-axis.
*   **FallingPlatform:** Platforms that crumble 0.5s after contact.
*   **Moving Lasers & Buttons:** Lethal moving beams and buttons to toggle them.

### Phase 2: Saving, HUD, and Meta-game
*   **save.json File:** Stores unlocked levels, collected Secrets, and Speedrun best times.
*   **Game States:** Linking `MainMenu`, `LevelSelect`, `PauseMenu`, and `Playing` screens.
*   **Secrets Menu (Cameos):** A dedicated menu section with 4 slots (initially question marks). Each of the 4 main levels hides a unique collectible sprite representing a character from the developer's future games. Once found, the character is unlocked in this menu.
*   **Replayability / Speedrun Time Bonuses:** If a player replays a level and visits an already-collected Secret location, they will find a "Time Bonus" item (a clock with a negative number, e.g., -5 seconds) instead of the character. This creates strategic speedrun routes where players must calculate if the detour is worth the time deduction!
*   **Minimalist HUD:** Only a level timer in the corner and a secret indicator. No hand-holding hints.
*   **Tutorials:** Parsing Tiled `Text` objects for unobtrusive background instructions (similar to Celeste).

### Phase 3: Polish & Juice
*   **VFX:** Dust particles on landing, trail effects during dashes.
*   **Animations:** Squish and stretch deformation during jumps and landings.
*   **Audio:** SFX (jumping, death, color swapping) and background music.
