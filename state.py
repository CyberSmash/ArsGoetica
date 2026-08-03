from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
import pygame_gui
import render
from pygame_gui.elements import UITextBox, UIButton

if TYPE_CHECKING:
    from app import App


class State:
    def on_init(self, app: App): ...

    def on_event(self, event: pygame.Event, app: App): ...
    def on_loop(self, app: App, dt: float): ...

    def on_render(self, app: App): ...

    def teardown(self, app: App): ...

class TitleScreen(State):
    def __init__(self):
        self.subtitle_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.start_button: pygame_gui.elements.UIButton | None = None

    def on_init(self, app: App):
        # Static text drawn with raw fonts (a serif suits the arcane theme);
        # only the interactive Start button uses pygame_gui.
        self.title_font = pygame.font.SysFont("georgia,timesnewroman,serif", 84)
        self.subtitle_font = pygame.font.SysFont("georgia,timesnewroman,serif", 30)
        cx = app.size[0] // 2
        self.start_button = UIButton(
            relative_rect=pygame.Rect(cx - 100, 440, 200, 60),
            text="Start",
            manager=app.ui,
        )

    def on_event(self, event: pygame.Event, app: App):
        app.ui.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.start_button:
            app.change_state(PlayGame())

    def on_loop(self, app: App, dt: float):
        pass  # app.on_loop already ticks the shared UIManager

    def on_render(self, app: App):
        surf = app._display_surf
        surf.fill((12, 10, 22))                       # dark backdrop
        cx = surf.get_width() // 2
        title = self.title_font.render("Ars Goetica", True, (198, 166, 92))
        subtitle = self.subtitle_font.render("Whispers of the Divine Tongue", True, (150, 142, 165))
        surf.blit(title, (cx - title.get_width() // 2, 170))
        surf.blit(subtitle, (cx - subtitle.get_width() // 2, 275))

    def teardown(self, app: App):
        self.start_button.kill()

class PlayGame(State):

    def __init__(self):
        self.inspector: UITextBox | None = None
        self.action_cell = ()

    def on_init(self, app: App):
        self.inspector = UITextBox(html_text="", relative_rect=(8, 8, 200, 250), manager=app.ui)

    def on_event(self, event: pygame.Event, app: App):
        overlay_keys = {
            pygame.K_f: render.Overlay.FUEL,
            pygame.K_b: render.Overlay.BURNING,
            pygame.K_t: render.Overlay.TEMP,
            pygame.K_ESCAPE: render.Overlay.NONE,
        }
        app.ui.process_events(event)

        app.input_handler.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key in overlay_keys:
            app.current_overlay = overlay_keys[event.key]
        if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
            x, y = app.player.get_action_cell()
            app.world.temp_c[y, x] += 400

    def on_loop(self, app: App, dt: float):
        intents = app.input_handler.drains()
        for agent in app.agents:
            for intent in intents:
                agent.controller.feed(intent)
            agent.controller.update(agent, app.world)
        app.sim.tick(dt, app.world)

        scale = app._display_surf.get_width() / app.main_surface.get_width()
        self.inspector.set_text(render.tile_inspector_text(app.world, render.get_mouse_cell(scale)))

    def on_render(self, app: App):
        render.draw_world(app.main_surface, app.world, app.sprites)
        render.draw_agent_sprites(app.main_surface, app.agents, app.agent_sprites)

        if app.current_overlay != render.Overlay.NONE:
            accessor, l, h = render.OVERLAY_RANGE[app.current_overlay]
            data = accessor(app.world)
            overlay = render.show_overlay(l, h, data)
            app.main_surface.blit(overlay)

        scale = app._display_surf.get_width() / app.main_surface.get_width()
        render.draw_mouse_cursor(app.main_surface, scale)
        render.show_action_square(app.main_surface, app.agents[0], app.agents[0].get_action_cell())
        render.draw_effects(app.main_surface, app.world, app.effect_sprites)
        pygame.transform.scale(app.main_surface, app._display_surf.get_size(), app._display_surf)
        pygame.transform.scale(app.main_surface, app._display_surf.get_size(), app._display_surf)

    def teardown(self, app: App):
        self.inspector.kill()
