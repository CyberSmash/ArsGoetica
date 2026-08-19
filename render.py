import pytmx
from intent import Intent
import material
from world import World
import pygame
from agent import Agent
import enum
from enum import auto
import numpy as np

class Overlay(enum.Enum):
    NONE = auto()
    FUEL = auto()
    TEMP = auto()
    BURNING = auto()

OVERLAY_RANGE = {
    Overlay.FUEL: (lambda w: w.fuel_c, 0, 400),
    Overlay.TEMP: (lambda w: w.temp_c, 60, 200),
    Overlay.BURNING: (lambda w: w.burning, 0, 1),
}

EFFECT_RULES = [
    (lambda w: w.burning, "flame")
]

def build_sprites(tmx: pytmx.TiledMap) -> dict[int, pygame.Surface]:
    return {
        material.ID_BY_NAME[p["material_name"]]: tmx.get_tile_image_by_gid(gid) 
            for gid, p in tmx.tile_properties.items()
            if p and "material_name" in p
    }

def build_agent_sprites(tmx: pytmx.TiledMap) -> dict[str, pygame.Surface]:
    # Iterate tile_properties (keyed by pytmx's actual gids) rather than computing
    # firstgid + local_id — pytmx compacts to referenced tiles, so that arithmetic
    # doesn't match its gid numbering. Mirrors build_sprites.
    return {
        p["agent_name"]: tmx.get_tile_image_by_gid(gid)
        for gid, p in tmx.tile_properties.items()
        if p and "agent_name" in p
    }

def build_effect_sprites(tmx: pytmx.TiledMap) -> dict[str, pygame.Surface]:
    return {
        p["effect_name"]: tmx.get_tile_image_by_gid(gid)
        for gid, p in tmx.tile_properties.items()
        if p and "effect_name" in p
    }

TILE_SIZE = 16

def draw_world(screen, world: World, sprites: dict[int, pygame.Surface]):
    for y in range(world.material.shape[0]):
        for x in range(world.material.shape[1]):
            screen.blit(sprites[world.material[y, x]], (x*TILE_SIZE, y*TILE_SIZE))

def draw_effects(screen, world: World, sprites: dict[int, pygame.Surface]):
    for fn, name in EFFECT_RULES:
        sprite = sprites[name]
        mask = fn(world)
        for row, col in np.argwhere(mask):
            screen.blit(sprite, (col*TILE_SIZE, row*TILE_SIZE))


def draw_agent_sprites(screen, agents: list[Agent], agent_sprites: dict[str, pygame.Surface]):
    agent: Agent
    for agent in agents:
        screen.blit(agent_sprites[agent.kind], (agent.x*TILE_SIZE, agent.y*TILE_SIZE))

def draw_overhead(screen, world: World, sprites: dict[int, pygame.Surface]):
    for y in range(world.material.shape[0]):
        for x in range(world.material.shape[1]):
            if not material.MATERIALS[world.material[y, x]].overhead:
                continue
            screen.blit(sprites[world.material[y, x]], (x * TILE_SIZE, y * TILE_SIZE))

def show_overlay(low: int, high: int, data: np.ndarray):
    h, w = data.shape
    overlay = pygame.Surface((w * TILE_SIZE, h * TILE_SIZE), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            t = data[y, x]
            frac = (t - low) / (high - low)
            frac = max(0.0, min(1.0, frac))
            if frac < 0.002:
                continue
                
            color = (255, int((1 - frac) * 255), 0, int(80 + frac * 175))
            rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            overlay.fill(color, rect)
    return overlay

def show_action_square(surface: pygame.Surface, agent_pos: Agent, action_square_loc: tuple):
    square = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    pygame.draw.rect(square, (255, 255, 255, 255), square.get_rect(), 1)
    surface.blit(square, (action_square_loc[0] * TILE_SIZE, action_square_loc[1] * TILE_SIZE))


def get_mouse_cell(scale: float):
    x, y = pygame.mouse.get_pos()
    cell_x = int(x / scale) // TILE_SIZE
    cell_y = int(y / scale) // TILE_SIZE

    return (cell_x, cell_y)

def draw_mouse_cursor(surface: pygame.Surface, scale: float):
    x, y = pygame.mouse.get_pos()
    cell_x = int(x / scale) // TILE_SIZE
    cell_y = int(y / scale) // TILE_SIZE
    hl = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    hl.fill((0, 255, 0, 100))

    surface.blit(hl, (cell_x * TILE_SIZE, cell_y * TILE_SIZE))

def tile_inspector_text(world, cell):
    cx, cy = cell
    
    mid = int(world.material[cy, cx])
    mat = material.MATERIALS[mid]
    return (
            f"cell: {cx, cy}<br>"
            f"mat:  {mat.name}<br>"
            f"temp: {world.temp_c[cy, cx]:.1f}<br>"
            f"ign:  {mat.ignition_temp:.1f}<br>"
            f"fuel: {world.fuel_c[cy,cx]:.1f}<br>"
            f"burn: {bool(world.burning[cy,cx])}<br>"
            f"cond: {mat.thermal_conductivity}")