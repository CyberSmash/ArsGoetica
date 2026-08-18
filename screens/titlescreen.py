
from screens.screen import Screen
from pygame_gui import UIManager
from pygame_gui.elements import UIButton
import pygame
from config import WINDOW_SIZE
import pygame_gui
from screens.gamescreen import GameScreen
from screens import nav

class TitleScreen(Screen):

    def __init__(self):
        self.ui_manager: UIManager = UIManager(WINDOW_SIZE)
        self.subtitle_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.start_button: UIButton | None = None
        self.title_font = pygame.font.SysFont("georgia,timesnewroman,serif", 84)
        self.subtitle_font = pygame.font.SysFont("georgia,timesnewroman,serif", 30)

        cx = WINDOW_SIZE[0] // 2
        self.start_button = UIButton(
            relative_rect=pygame.Rect(cx - 100, 440, 200, 60),
            text="Start",
            manager=self.ui_manager,
        )

    def update(self, stack: "ScreenStack", dt: float, focused: bool):
        self.ui_manager.update(dt)

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((12, 10, 22))  # dark backdrop
        cx = surf.get_width() // 2
        title = self.title_font.render("Ars Goetica", True, (255, 255, 255))
        subtitle = self.subtitle_font.render("Whispers of the Divine Tongue", True, (150, 150, 150))
        surf.blit(title, (cx - title.get_width() // 2, 170))
        surf.blit(subtitle, (cx - subtitle.get_width() // 2, 275))
        self.ui_manager.draw_ui(surf)

    def handle_event(self, stack: "ScreenStack", event: pygame.Event):
        self.ui_manager.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.start_button:
            nav.to_game(stack)
