from screens.screen import Screen
from pygame_gui import UIManager
from pygame_gui.elements import UITextBox
import render
from input_handler import InputHandler
from sim import Simulation
import pygame
from level import Level
from config import WINDOW_SIZE
from screens.screenstack import ScreenStack
from pytmx import load_pygame
from screens import nav
import config

class GameScreen(Screen):

    def __init__(self, map_path: str = "map1.tmx"):
        self.ui_manager: UIManager = UIManager(WINDOW_SIZE)
        self.level: Level | None = None
        self.inspector: UITextBox | None = UITextBox(html_text="", relative_rect=(8, 8, 200, 250), manager=self.ui_manager)
        self.action_cell = ()
        self.current_overlay : render.Overlay = render.Overlay.NONE
        self.sim: Simulation | None = None
        self.input_handler: InputHandler | None = None
        self.map_path = map_path
        self.main_surface: pygame.Surface | None = None
        self.sprites: dict[int, pygame.Surface] = dict()
        self.scale : float = 1.0
        self.agent_sprites: dict[str, pygame.Surface] = dict()
        self.effect_sprites: dict[str, pygame.Surface] = dict()
        self.stack : ScreenStack | None = None

    def on_enter(self, stack: ScreenStack) -> None:

        tmx = load_pygame(self.map_path)
        self.level = Level.from_tmx(tmx)
        self.sprites = render.build_sprites(tmx)
        self.agent_sprites = render.build_agent_sprites(tmx)
        self.effect_sprites = render.build_effect_sprites(tmx)
        h, w = self.level.world.material.shape
        self.main_surface = pygame.Surface((w * config.TILE_SIZE, h * config.TILE_SIZE))
        self.scale = WINDOW_SIZE[0] / self.main_surface.get_width()
        self.input_handler = InputHandler()
        self.sim = Simulation()
        self.stack = stack

    def handle_event(self, stack: ScreenStack, event: pygame.Event):
        self.ui_manager.process_events(event)

        overlay_keys = {
            pygame.K_f: render.Overlay.FUEL,
            pygame.K_b: render.Overlay.BURNING,
            pygame.K_t: render.Overlay.TEMP,
            #pygame.K_ESCAPE: render.Overlay.NONE,
        }

        if event.type == pygame.KEYDOWN and event.key in overlay_keys:
            self.current_overlay = overlay_keys[event.key]
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            nav.quit_to_title(stack)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            nav.open_cast(stack)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
            x, y = self.level.player.get_action_cell()
            self.level.world.temp_c[y, x] += 400
        self.input_handler.handle_event(event)


    def update(self, stack: "ScreenStack", dt: float, focused: bool):
        intents = self.input_handler.drains()
        for agent in self.level.agents:
            for intent in intents:
                agent.controller.feed(intent)
            agent.controller.update(agent, self.level.world)
        self.sim.tick(dt, self.level.world)


        self.inspector.set_text(render.tile_inspector_text(self.level.world, render.get_mouse_cell(self.scale)))
        self.ui_manager.update(dt)

    def draw(self, surf: pygame.Surface) -> None:
        render.draw_world(self.main_surface, self.level.world, self.sprites)
        render.draw_agent_sprites(self.main_surface, self.level.agents, self.agent_sprites)

        if self.current_overlay != render.Overlay.NONE:
            accessor, l, h = render.OVERLAY_RANGE[self.current_overlay]
            data = accessor(self.level.world)
            overlay = render.show_overlay(l, h, data)
            self.main_surface.blit(overlay)


        render.draw_mouse_cursor(self.main_surface, self.scale)
        render.show_action_square(self.main_surface, self.level.player, self.level.player.get_action_cell())
        render.draw_effects(self.main_surface, self.level.world, self.effect_sprites)

        pygame.transform.scale(self.main_surface, surf.get_size(), surf)
        self.ui_manager.draw_ui(surf)