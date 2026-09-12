import numpy as np
import dataclasses
import pytmx
from pytmx import TiledMap
from material import MATERIAL_ID_BY_NAME, ALL_UNIQUE_MATERIALS, material_lookup

AMBIENT_C = 20.0

DEFAULT_MATERIAL = MATERIAL_ID_BY_NAME["dirt"]

@dataclasses.dataclass
class World:

    material: np.ndarray
    temp_c: np.ndarray
    fuel_c: np.ndarray
    burning: np.ndarray
    visual: np.ndarray
    # material id -> a representative gid, so a material transition (burns_into)
    # can pick a sprite. material->gid isn't 1:1, so we keep one gid per material.
    rep_gid: np.ndarray

    @classmethod
    def from_tmx(cls, tmx: TiledMap) -> "World":
        material = np.zeros((tmx.height, tmx.width), dtype=np.int32)
        visual = np.zeros((tmx.height, tmx.width), dtype=np.int32)

        # pytmx renumbers gids into a compact internal scheme, so iter_data()
        # yields internal gids, not the real (global) gid. Invert the gidmap to
        # recover the real gid, then subtract the tileset's firstgid to get the
        # LOCAL tile id -- the number Tiled shows in the tileset panel and uses
        # for <tile id="..."> in the .tsx, i.e. what you actually go tag.
        real_by_internal = {
            internal: real
            for real, variants in tmx.gidmap.items()
            for internal, _flags in variants
        }

        def local_id(internal_gid: int) -> int:
            real = real_by_internal.get(internal_gid, internal_gid)
            ts = max((t for t in tmx.tilesets if t.firstgid <= real),
                     key=lambda t: t.firstgid, default=None)
            return real - ts.firstgid if ts else real

        # One representative gid per material, for material->gid at transition time
        # (e.g. burns_into). Built from all tagged tiles in the tileset, so even a
        # material that's never placed on this map (a burns_into target like dirt)
        # still resolves to a sprite. Last tagged tile of a given material wins.
        rep_gid = np.zeros(len(ALL_UNIQUE_MATERIALS), dtype=np.int32)
        for g, p in tmx.tile_properties.items():
            if p and "material_name" in p:
                rep_gid[MATERIAL_ID_BY_NAME[p["material_name"]]] = g

        for layer in tmx.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, gid in layer.iter_data():
                if gid == 0:
                    continue
                props = tmx.get_tile_properties_by_gid(gid)
                name = props.get("material_name") if props else None
                assert name, (
                    f"Untagged tile at {(x, y)} in layer '{layer.name}': "
                    f"tileset tile id {local_id(gid)}. Give it a "
                    f"material_name (use 'void' for pure decoration)."
                )
                material[y, x] = MATERIAL_ID_BY_NAME[name]
                visual[y, x] = gid

        return cls.from_material(material, visual, rep_gid)

    @classmethod
    def from_material(cls, material: np.ndarray, visual: np.ndarray | None = None,
                      rep_gid: np.ndarray | None = None) -> "World":
        if visual is None:
            visual = material.copy()
        if rep_gid is None:
            # No gid info (material-only path): identity, so visual stays consistent
            # with material for callers that aren't tmx-backed.
            rep_gid = np.arange(len(ALL_UNIQUE_MATERIALS), dtype=np.int32)
        return cls(material=material,
                   visual=visual,
                   rep_gid=rep_gid,
                   temp_c=np.full(material.shape, AMBIENT_C, dtype=np.float32),
                   fuel_c=material_lookup("max_fuel_c")[material],
                   burning=np.zeros(material.shape, dtype=bool)
        )

    def in_bounds(self, x: int, y: int) -> bool:
        h, w = self.material.shape
        return 0 <= x < w and 0 <= y < h
    
    def is_passable(self, x: int, y: int) -> bool:

        if not self.in_bounds(x, y):
            return False
        return not ALL_UNIQUE_MATERIALS[self.material[y, x]].solid


def find_spawn(tmx: pytmx.TiledMap) -> tuple[int, int]:
    for obj in tmx.objects:
        if obj.name == "player_spawn":
            return int(obj.x // tmx.tilewidth), int(obj.y // tmx.tileheight)

    raise ValueError("no player_spawn found.")