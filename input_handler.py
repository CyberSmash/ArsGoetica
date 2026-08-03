import pygame
from intent import Intent
class InputHandler:
    def __init__(self):
        self.bindings = {
            pygame.K_UP: Intent.MOVE_UP,
            pygame.K_LEFT: Intent.MOVE_LEFT,
            pygame.K_RIGHT: Intent.MOVE_RIGHT,
            pygame.K_DOWN: Intent.MOVE_DOWN,
        }

        self.pending = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in self.bindings:
            self.pending.append(self.bindings[event.key])

    def drains(self):
        intents, self.pending = self.pending, []
        return intents