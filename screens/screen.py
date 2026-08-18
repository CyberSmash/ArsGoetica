from abc import ABC, abstractmethod

import pygame


class Screen(ABC):
    def on_enter(self, stack: "ScreenStack") -> None: ...
    def on_exit(self) -> None: ...
    def on_reveal(self) -> None: ...
    def on_obscure(self) -> None: ...

    @abstractmethod
    def handle_event(self, stack: "ScreenStack",  event: pygame.Event): ...

    @abstractmethod
    def update(self, stack: "ScreenStack", dt: float, focused: bool): ...

    @abstractmethod
    def draw(self, surf: pygame.Surface) -> None: ...

    def blocks_update_below(self) -> bool:
        return True

    # Fills the window, don't bother drawing things underneith.
    def opaque(self) -> bool:
        return True
