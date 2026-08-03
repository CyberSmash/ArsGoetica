import pygame
from pytmx.util_pygame import load_pygame
import pytmx
from world import World
import render
from agent import Agent
from input_handler import InputHandler
from player_controller import PlayerController
from sim import Simulation
import pygame_gui
from pygame_gui.elements import UITextBox
from intent import Intent
from state import PlayGame, TitleScreen, State

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.weight, self.height = 960, 640
        self.world = None
        self.player: Agent | None = None

        self.agents: list[Agent] = []   
        self.agent_sprites: dict[str, pygame.Surface] = dict()
        self.input_handler = InputHandler()
        self.current_overlay = render.Overlay.NONE
        self.sim = Simulation()
        self.ui: pygame_gui.UIManager | None = None
        self.inspector: UITextBox | None = None
        self.move_intent: Intent = Intent.MOVE_NONE
        self.tmx_data: pytmx.TiledMap | None = None
        self.sprites: dict[int, pygame.Surface] = dict()
        self.state: State | None = None
        self.effect_sprites: dict[int, pygame.Surface] = dict()

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.ui = pygame_gui.UIManager(self.size, theme_path="theme.json")

        self._running = True
    
        self.tmx_data: pytmx.TiledMap = load_pygame("map1.tmx")
        self.world = World.from_tmx(self.tmx_data)

        self.sprites = render.build_sprites(self.tmx_data)
        self.agent_sprites = render.build_agent_sprites(self.tmx_data)
        self.effect_sprites = render.build_effect_sprites(self.tmx_data)
        spawn_point = self.find_spawn(self.tmx_data)
        self.player = Agent(*spawn_point, kind="wizard", controller=PlayerController())
        
        self.agents.append(self.player)

        w = self.tmx_data.tilewidth * self.tmx_data.width
        h = self.tmx_data.tileheight * self.tmx_data.height
        self.main_surface = pygame.Surface((w, h))
        self.change_state(TitleScreen())

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        self.state.on_event(event, self)

    def on_loop(self, dt: float):
        self.ui.update(dt)
        self.state.on_loop(self, dt)


    def on_render(self):
        self.state.on_render(self)
        self.ui.draw_ui(self._display_surf)
        pygame.display.flip()
        
    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        clock = pygame.time.Clock()
        while( self._running ):
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop(dt)
            self.on_render()
        self.on_cleanup()

    def find_spawn(self, tmx: pytmx.TiledMap) -> tuple[int, int]:
        for obj in tmx.objects:
            if obj.name == "player_spawn":
                return int(obj.x // tmx.tilewidth), int(obj.y // tmx.tileheight)

        raise ValueError("no player_spawn found.")

    def change_state(self, new_state: State):
        if self.state is not None:
            self.state.teardown(self)

        self.state = new_state
        self.state.on_init(self)