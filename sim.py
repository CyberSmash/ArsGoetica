from world import World
import numpy as np
from world import AMBIENT_C
import material
COOLING_RATE = 0.1

_N = len(material.MATERIALS)
IGNITION_LOOKUP = material.material_lookup("ignition_temp")
BURN_HEAT_LOOKUP = material.material_lookup("burn_heat_c") 
BURNS_INTO_LOOKUP = np.array([material.ID_BY_NAME[m.burns_into] if (m := material.MATERIALS[i]).burns_into else i for i in range(_N)], dtype=np.int32)
FLAMMABLE_LOOKUP = np.isfinite(IGNITION_LOOKUP)   # True where ignition_temp < inf

class Simulation(object):
    SIM_HZ = 10
    SIM_DT = 1 / SIM_HZ
    DIFFUSION_K = 0.20

    def __init__(self):
        self._accumulator = 0.0

    def tick(self, dt: float, world: World):
        self._accumulator += dt
        while self._accumulator >= self.SIM_DT:
            self._accumulator -= self.SIM_DT
            self.diffuse(world)
            self.combust(world)
            self.radiate(world)
            self.cool(world)

    def diffuse(self, world: World):
        # This is fancy numpy stuff for giving me
        # all the cells in the map's conductivities. As world.material, gives me 
        # the material ids, this gives me the same map, but is thermal conductivity.
        cond = material.COND_TABLE[world.material]
        t = world.temp_c

        k_n = np.minimum(cond, np.roll(cond, 1, axis=0))
        k_s = np.minimum(cond, np.roll(cond, -1, axis=0))
        k_e = np.minimum(cond, np.roll(cond, -1, axis=1))
        k_w = np.minimum(cond, np.roll(cond, 1, axis=1))
  
        flow_n = k_n * (np.roll(t, 1, axis=0) - t)
        flow_s = k_s * (np.roll(t, -1, axis=0) - t)
        flow_e = k_e * (np.roll(t, -1, axis=1) - t)
        flow_w = k_w * (np.roll(t, 1, axis=1) - t)

        world.temp_c = t + flow_n + flow_s + flow_e + flow_w

    def cool(self, world: World):
        world.temp_c += COOLING_RATE * (AMBIENT_C - world.temp_c)

    def combust(self, world: World):
        mat = world.material
        ignition = IGNITION_LOOKUP[mat]
        burn_heat = BURN_HEAT_LOOKUP[mat]

        new_burning = (world.temp_c > ignition) & (world.fuel_c > 0 ) & ~world.burning
        world.burning |= new_burning

        b = world.burning
        world.temp_c[b] += burn_heat[b]
        world.fuel_c[b] -= burn_heat[b]
        burnt = world.burning & (world.fuel_c <= 0)
        world.material[burnt] = BURNS_INTO_LOOKUP[mat][burnt]

        world.burning[burnt] = False
        world.fuel_c[burnt] = 0.0

    def radiate(self, world: World):
        RADIANT_HEAT = 120
        r = np.where(world.burning, RADIANT_HEAT, 0.0)
        incoming = np.roll(r, 1, 0) + np.roll(r, -1, 0) + np.roll(r, 1, 1) + np.roll(r, -1, 1)
        fuel_ahead = ~world.burning & FLAMMABLE_LOOKUP[world.material]
        world.temp_c += incoming * fuel_ahead
