import dataclasses
import itertools
import numpy as np

@dataclasses.dataclass
class Material:
    name: str

    # Right now this is whether the tile is walkable or not.
    solid: bool = False

    # How well heat spreads to this material.
    thermal_conductivity: float = 0.1
    ignition_temp: float = float("inf")

    # The rate that fuel is burned. This is also in temperature, and applies every frame update.
    burn_heat_c: float = 0.0

    # The maximum amount of fuel something has, in units of C.
    # Note that this represents temperature, not raw energy. 
    max_fuel_c: float = 0.0

    # Material name that this turns into when fuel is zero.
    burns_into: str | None = "dirt"

    # BG color
    base_tint: tuple = (0, 0, 0)

    # Determines the draw order
    overhead: bool = False

_next_id = itertools.count()

ALL_UNIQUE_MATERIALS: dict[int, Material] = {}
MATERIAL_ID_BY_NAME: dict[str, int] = {}

def register(mat: Material) -> int:
    mid = next(_next_id)
    ALL_UNIQUE_MATERIALS[mid] = mat
    MATERIAL_ID_BY_NAME[mat.name] = mid
    return mid

def material_lookup(field: str) -> np.ndarray:
    return np.array([getattr(ALL_UNIQUE_MATERIALS[i], field) for i in range(len(ALL_UNIQUE_MATERIALS))])

AIR_THERMAL_CONDUCTIVITY = 0.15

STONE_WALL = register(Material("stone_wall", 
                               solid=True, 
                               thermal_conductivity=0.00)
                               )

STONE_FLOOR = register(Material("stone_floor", 
                                thermal_conductivity=AIR_THERMAL_CONDUCTIVITY)
                                )
WALL_TOPPER = register(Material("wall_topper", 
                                solid=False, 
                                thermal_conductivity=AIR_THERMAL_CONDUCTIVITY, 
                                overhead=True)
                                )

STONE_TOWER = register(Material("stone_tower", 
                                solid=True, 
                                thermal_conductivity=0.00)
                                )

STONE_PAVER_BROKEN = register(Material("stone_paver_broken", 
                                       thermal_conductivity=AIR_THERMAL_CONDUCTIVITY))

WOOD_FLOOR = register(Material("wood_floor", 
                               thermal_conductivity=AIR_THERMAL_CONDUCTIVITY, 
                               ignition_temp=250,
                               burn_heat_c=60,
                               max_fuel_c=3000))

WOOD_DOOR = register(Material("wood_door", 
                              solid=True, 
                              thermal_conductivity=0.05, 
                              max_fuel_c=3000,
                              burn_heat_c=60,
                              ignition_temp=350,
                              ))
DIRT = register(Material("dirt", 
                         thermal_conductivity=AIR_THERMAL_CONDUCTIVITY)
                         )

DIRT_PATH_VERT = register(Material("dirt_path_vert", 
                                   thermal_conductivity=0.01)
                          )

GRASS = register(Material("grass", 
                          thermal_conductivity=0.12, 
                          max_fuel_c=500, 
                          ignition_temp=250, 
                          burn_heat_c=60, 
                          burns_into="dirt"))

DRY_GRASS = register(Material("grass_dry", 
                              thermal_conductivity=0.12, 
                              max_fuel_c=500, 
                              ignition_temp=250, 
                              burn_heat_c=60, 
                              burns_into="dirt"))

FLOWERS = register(Material("flowers", 
                            thermal_conductivity=0.12, 
                            max_fuel_c=600, 
                            ignition_temp=250, 
                            burn_heat_c=60, 
                            burns_into="dirt"))

WINDOW = register(Material("window", 
                           solid=True, 
                           thermal_conductivity=0.05))

DOOR = register(Material("door",
                         solid=False,
                         thermal_conductivity=0.0))

TREE = register(Material("tree",
                         solid=True,
                         thermal_conductivity=0.05,
                         max_fuel_c=10000,
                         ignition_temp=700))

DIRT_PATH_ELBOW = register(Material("dirt_path_elbow",
                         thermal_conductivity=AIR_THERMAL_CONDUCTIVITY))

# Explicit "no physics" material. Tag purely decorative tiles with material_name
# "void" so intent is stated, not guessed. Passable, non-flammable, air-like heat
# so it behaves as neutral empty space. Untagged tiles are still a hard error.
VOID = register(Material("void",
                         solid=False,
                         thermal_conductivity=AIR_THERMAL_CONDUCTIVITY))

# Footgun - This needs to happen AFTER all materials are registered. If not
# it won't work properly. This may be a problem in the future with TOML files, or
# any material defined outside of this file. BEWARE.
COND_TABLE = np.array([m.thermal_conductivity for k, m in ALL_UNIQUE_MATERIALS.items()])