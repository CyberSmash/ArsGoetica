import pygame
from screens.titlescreen import TitleScreen
from screens.screenstack import ScreenStack

class App:
    def __init__(self):
        self._running = True
        self.display_surf = None
        self.size = self.weight, self.height = 960, 640
        self.screen_stack = ScreenStack()

    def on_init(self):
        pygame.init()
        self.display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)

        self._running = True
        self.screen_stack.push(TitleScreen())
        self.screen_stack.apply_pending()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        self.on_init()
        clock = pygame.time.Clock()
        while  self._running and len(self.screen_stack):
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                else:
                    self.screen_stack.handle_event(event)

            self.screen_stack.update(dt)
            self.screen_stack.apply_pending()
            self.screen_stack.draw(self.display_surf)
            pygame.display.flip()
        self.on_cleanup()
