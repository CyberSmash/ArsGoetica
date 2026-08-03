import numpy as np
import dataclasses
import pytmx
from pytmx import TiledMap
from material import ID_BY_NAME, MATERIALS, material_lookup

AMBIENT_C = 20.0

@dataclasses.dataclass
class World:

    material: np.ndarray
    temp_c: np.ndarray
    fuel_c: np.ndarray
    burning: np.ndarray

    @classmethod
    def from_tmx(cls, tmx: TiledMap) -> "World":
        material = np.zeros((tmx.height, tmx.width), dtype=np.int32)

        for layer in tmx.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, image in layer.iter_data():
                if image == 0:
                    continue
                #surface.blit(image, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))
                props = tmx.get_tile_properties_by_gid(image)
                name = props.get("material_name") if props else None
                assert name, f"Untagged tile at: {x, y} in layer: {layer.name}"
                material[y, x] = ID_BY_NAME[name]

        return cls.from_material(material)
    
    @classmethod
    def from_material(cls, material: np.ndarray) -> "World":
        return cls(material=material, 
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
        return not MATERIALS[self.material[y, x]].solid