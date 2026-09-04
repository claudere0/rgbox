# 🎮 RGBox

**RGBox** is a precision puzzle-platformer built entirely from scratch using Python and Pygame-CE.
The game is built around a custom 2D physics engine and a robust Finite State Machine, focusing on additive RGB color mixing and world-inversion mechanics.

<video src="https://github.com/user-attachments/assets/b9de4696-bd0d-4287-bc25-af6c1e7c11dd" autoplay loop muted playsinline width="100%"></video>

* 🪟 [Download for Windows](https://github.com/claudere0/rgbox/releases/download/v1.0.0/rgbox_windows.zip)
* 🍎 [Download for Mac (Apple Silicon)](https://github.com/claudere0/rgbox/releases/download/v1.0.0/rgbox_mac.zip)

## 🌟 The Core Concept
You control a cube that absorbs light pigments from "Color Stations".
*   **The Inversion:** If the cube has no colors (Black), the world's background is White and the platforms are Black. As soon as the cube absorbs any color, the world instantly inverts (Background turns Black, platforms turn White), making the cube glow in the dark.
*   **Additive Mixing:** You can mix Red, Green, and Blue pigments to create Yellow, Cyan, Magenta, and White.
*   **Dynamic Size:** The more colors you absorb, the larger the cube becomes! (Black = 40px, White = 88px).
*   **Color Doors:** Solid barriers that only let you pass if your current color perfectly matches the door's color. You must constantly drop and pick up colors to navigate the facility.

## ⚡ Abilities
Abilities are tied strictly to the pigments you currently hold:
*   🟥 **Red (R):** Unlocks the **Dash** ability (LShift).
*   🟩 **Green (G):** Unlocks the **Double Jump** (Space in mid-air).
*   🟦 **Blue (B):** Unlocks **Wall Slide & Wall Jump** (Hold against a wall).

By mixing colors, you combine their abilities (e.g., holding Yellow allows you to Dash AND Double Jump!).

## 🛠️ Engine & Technical Architecture
This game does not use a commercial engine (like Unity or Godot). The engine was built from scratch in Python.

### 1. Physics & State Machine (FSM)
*   **Custom AABB Collisions:** Axis-separated collision resolution ensures the player never gets stuck on corners.
*   **State Machine:** The player's logic is cleanly divided into `Idle`, `Run`, `Jump`, `Fall`, `WallSlide`, `Dash`, and `Death` states.
*   **Game Feel / QoL:** Features like **Coyote Time** (jumping just after leaving a ledge) and adaptive gravity (falling is faster than jumping upwards).

### 2. Level Design & Parsing
*   Levels are built using the **Tiled** map editor (`.tmx` files) and parsed dynamically using `pytmx`.
*   Interactive elements include: Moving Lasers, Timer Buttons, Bounce Pads, Crumbling Platforms, and Color Stations.

### 3. Polish, Juice & VFX
*   **Squish & Stretch:** The visual rectangle (`display_rect`) deforms smoothly via `lerp` math during jumps and landings, completely decoupled from the strict physical hitbox.
*   **Particle System:** Kinetic dust particles spawn based on the player's physical velocity (`impact_vel ** 0.5`) and surface area. Dash trails leave a fading ghost effect.
*   **Audio Engine:** Seamless background music fading and state-driven SFX.

### 4. Meta-Systems
*   **Save System (`save.json`):** Tracks unlocked levels, stores the player's best speedrun times (down to the millisecond), and remembers fullscreen preferences.
*   **Secrets & Speedrunning:** Hidden 'Cameo' characters can be collected in the levels. Replaying levels where secrets were already found spawns a 'Time Bonus' clock that subtracts seconds from your speedrun timer!

## 🚀 How to Play (Developer Setup)
1. Ensure you have Python 3.11+ installed.
2. Install the required libraries:
   ```bash
   pip install pygame-ce pytmx
   ```
3. Run the game:
   ```bash
   python3 main.py
   ```

## 🎮 Controls
*   **A / D** or **Left / Right Arrows:** Move
*   **Spacebar:** Jump (and Double Jump if Green)
*   **LShift:** Dash (if Red)
*   **E:** Interact with Color Stations
*   **Esc:** Pause Menu
