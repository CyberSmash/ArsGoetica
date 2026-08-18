from dataclasses import dataclass
import pygame

_FONTS: dict[int, pygame.font.Font] = {}


def font(size: int) -> pygame.font.Font:
    if size not in _FONTS:  # font construction is slow; never do it per frame
        _FONTS[size] = pygame.font.SysFont("consolas,dejavusansmono,monospace", size)
    return _FONTS[size]


def text(surf: pygame.Surface, msg: str, x: int, y: int, size: int, color) -> None:
    surf.blit(font(size).render(msg, True, color), (x, y))


def dim(surf: pygame.Surface, alpha: int) -> None:
    veil = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, alpha))
    surf.blit(veil, (0, 0))


@dataclass
class Menu:
    items: list[str]
    selected: int = 0

    def handle_event(self, event: pygame.event.Event) -> int | None:
        """Returns the chosen index, or None."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.items)
        elif event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.items)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.selected
        return None

    def draw(self, surf: pygame.Surface, title: str, x: int, y: int) -> None:
        text(surf, title, x, y, 34, (235, 235, 245))
        for i, item in enumerate(self.items):
            on = i == self.selected
            prefix = "> " if on else "  "
            color = (250, 220, 90) if on else (140, 140, 150)
            text(surf, prefix + item, x, y + 60 + i * 34, 24, color)
