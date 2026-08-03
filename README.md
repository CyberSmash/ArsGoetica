# 🔥 Ars Goetica
### *Whispers of the Divine Tongue*

> A fantasy game where you **discover** magic instead of unlocking it — spells are incantations you compose from an invented lexicon, and the world responds not to *spells* but to the *properties* they emit. Fire doesn't melt ice because someone wrote `fire melts ice`. Fire emits heat; ice has a melting threshold; the rest is physics. 🧙‍♂️✨

A weekend-scale **pygame prototype** for an emergent spellcraft sim. Deliberately throwaway — the goal is to prove the mechanics before a proper build in C++/raylib. 🛠️

---

## 🌌 The Big Idea

The world is a **cellular automaton of properties**, not a script of special cases:

- 💥 **Effects emit properties** — fire emits heat (with a magnitude), and that's all it knows how to do.
- 🧱 **Materials respond to thresholds** — grass ignites at ~250°, wood at ~300°, stone never.
- 🎲 **Depth is emergent** — 50 spells × 50 materials isn't 2,500 scripts; it's ~100 definitions that meet at runtime. Any heat source melts, burns, or bursts anything, for free.

The magic that isn't written down is the whole point. 🔮

---

## 🎇 What Works Today

- 🗺️ **Tiled map loading** — TMX → an integer `material` grid (struct-of-arrays, no `Tile` class).
- 🧪 **Data-driven materials** — one `Material` dataclass + registry; behavior comes from *data*, never `if material == X`.
- 🔥 **A real fire simulation:**
  - 🌡️ Conductivity-weighted **heat diffusion** (walls dam the flow)
  - ❄️ **Cooling** back toward ambient
  - 🪵 **Combustion** — ignition thresholds, fuel reservoirs, and char transitions (grass → dirt)
  - 📡 **Radiant spread** — burning fuel preheats its neighbors, so fire *propagates* instead of just diffusing
  - 🛤️ **Firebreaks emerge** — a dirt path with no fuel stops the blaze; wider paths are safer
- ⏱️ **Fixed-timestep sim** decoupled from the render loop (framerate-independent, deterministic, pausable).
- 🧙 **Grid movement** — event-driven input → intents → collision-checked moves.
- 🎮 **Interchangeable controllers** — keyboard and (future) AI plug into the same socket via a `Protocol`.
- 🖥️ **Debug tooling** — heat/fuel/burning overlays, a live tile inspector, and mouse-snapped cursor.
- 🏰 **State machine** — a title screen and gameplay state.

---

## 🚀 Getting Started

```bash
# from the project directory
python3 -m venv venv
./venv/bin/pip install pygame-ce pytmx pygame_gui numpy
./venv/bin/python main.py
```

> 🎨 **Assets:** the tilesets currently reference the [Kenney 1-bit pack](https://kenney.nl/assets/1-bit-pack). The map expects it at `../Downloads/kenney_1-bit-pack/` relative to the project — adjust the `.tsx` paths (or drop the pack into an `assets/` folder) if yours lives elsewhere.

---

## 🕹️ Controls

| Key / Input | Action |
|---|---|
| ⬆️ ⬇️ ⬅️ ➡️ | Move the wizard (one tile per press) |
| `1` | 🔥 Drop heat on your tile (light the world up) |
| `T` | 🌡️ Temperature overlay |
| `F` | 🪵 Fuel overlay |
| `B` | 🔥 Burning overlay |
| `Esc` | Clear overlay |
| 🖱️ Hover | Inspect a tile (material, temp, fuel, burning) |

---

## 🧭 Architecture at a Glance

The load-bearing rules that keep it emergent instead of scripted:

- 🌊 **Fields vs. agents** — fields are numpy arrays evolving by local rules; agents read/write the field but the field never knows about them.
- 📚 **Overlays, not objects** — one `material` grid + parallel `temp_c` / `fuel_c` / `burning` sheets; a "tile" is a column across them.
- 🧩 **Modules own behavior, the app owns instances** — `render.py` and `sim.py` are stateless functions/classes; the `App` holds the world, agents, and surfaces.
- 🚫 **`sim/` never imports pygame** — the simulation is pure numbers.
- 🎯 **Controllers emit intent; agents resolve it** — so keyboard and AI are interchangeable.

```
main.py            # launcher
app.py             # App: window, game loop, owns world + agents + surfaces
state.py           # state machine — TitleScreen, PlayGame
world.py           # World: material + temp/fuel/burning overlays, TMX loader
material.py        # Material dataclass + registry (data-driven)
sim.py             # Simulation: diffuse → combust → radiate → cool
agent.py           # Agent + Controller protocol
player_controller.py  # keyboard-driven controller
input_handler.py   # keyboard → Intent
intent.py          # Intent enum (value-carrying, .delta)
render.py          # world / agents / overlays / inspector / cursor
```

---

## 🔭 Roadmap

- ✅ Map loading, property-based fire sim, player movement, debug tooling, state machine
- 🔜 **Incantation parser** — type spells (`igni`, `igni vast`, `glaci then igni`…) that emit properties
- 🔮 Item modifiers → sigils → shields → spell proficiency → more properties (moisture, charge, pressure)

Each layer earns its place only once the one before it works. Emergence rewards patience. 🌱

---

## 🪄 Philosophy

> Don't hide the answer — *remove* it. A wiki can document every root and property and still never capture what happens when *this* player chains them in *this* biome against *this* material. The vocabulary is knowable; the poetry isn't.

*Built with Python, [pygame-ce](https://pyga.me/), [pytmx](https://github.com/bitcraft/pytmx), [pygame_gui](https://github.com/MyreMylar/pygame_gui), and numpy.* 💜
