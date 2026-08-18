from screens.screen import Screen
from pygame_gui import UIManager
from pygame_gui.elements import UITextEntryBox, UITextEntryLine
import config
import pygame

class SpellCast(Screen):

    def __init__(self) -> None:
        self.ui_manager = UIManager(config.WINDOW_SIZE)
        #cx = config.WINDOW_SIZE[0] // 2
        #self.entry = UITextEntryBox(relative_rect=pygame.Rect(cx - 100, 440, 200, 100), manager=self.ui_manager)

    def on_enter(self, stack: "ScreenStack") -> None:
        cx = config.WINDOW_SIZE[0] // 2
        width = config.WINDOW_SIZE[0] - 100
        left = 50
        self.entry = self.entry = UITextEntryLine(relative_rect=pygame.Rect(left, 440, width, 50), manager=self.ui_manager)
        self.entry.focus()

    def update(self, stack: "ScreenStack", dt: float, focused: bool):
        self.ui_manager.update(dt)

    def draw(self, surf: pygame.Surface) -> None:
        self.ui_manager.draw_ui(surf)

    def handle_event(self, stack: "ScreenStack", event: pygame.Event):
        self.ui_manager.process_events(event)
