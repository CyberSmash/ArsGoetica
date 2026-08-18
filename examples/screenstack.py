"""Pushdown screen stack for pygame: menus, pause, and text dialogs.

    python screen_stack.py

Arrows move / navigate, SPACE talks to the NPC, ENTER selects, ESC pauses
and backs out of menus.

Requires Python 3.10+ (match statement) and pygame 2.x.
"""

from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field

import pygame

WIDTH, HEIGHT = 800, 600

# Purely for the demo: makes the callback ordering visible on screen.
EVENT_LOG: deque[str] = deque(maxlen=8)


def log(msg: str) -> None:
    EVENT_LOG.append(msg)


# --------------------------------------------------------------------- Screen
class Screen(ABC):
    """One layer of the UI. The stack owns it; it never owns the stack."""

    # --- lifecycle. Note obscure/reveal are NOT exit/enter: a pause menu
    # --- pushed on top of gameplay obscures it, it does not tear it down.
    def on_enter(self, stack: "ScreenStack") -> None: ...
    def on_exit(self) -> None: ...
    def on_obscure(self) -> None: ...
    def on_reveal(self) -> None: ...

    # Only ever called for the topmost screen. That single rule is what makes
    # modality free -- no screen needs to know whether a menu is open above it.
    def handle_event(self, stack: "ScreenStack", event: pygame.event.Event) -> None: ...

    @abstractmethod
    def update(self, stack: "ScreenStack", dt: float, focused: bool) -> None: ...

    @abstractmethod
    def draw(self, surf: pygame.Surface) -> None: ...

    # False lets the screen below keep ticking (HUD overlay, toast, subtitle).
    def blocks_update_below(self) -> bool:
        return True

    # True means "I fill the window opaquely, don't bother drawing under me".
    def opaque(self) -> bool:
        return True


# ------------------------------------------------------------ stack commands
@dataclass
class Push:
    screen: Screen


@dataclass
class Pop:
    pass


@dataclass
class Replace:
    screen: Screen


@dataclass
class PopTo:
    target: type


@dataclass
class Reset:
    screen: Screen


Command = Push | Pop | Replace | PopTo | Reset


class ScreenStack:
    def __init__(self) -> None:
        self._stack: list[Screen] = []
        self._pending: list[Command] = []

    # ---- queueing API. Nothing here mutates the stack; see apply_pending.
    def push(self, screen: Screen) -> None:
        self._pending.append(Push(screen))

    def pop(self) -> None:
        self._pending.append(Pop())

    def replace(self, screen: Screen) -> None:
        self._pending.append(Replace(screen))

    def pop_to(self, target: type) -> None:
        """Unwind until `target` is on top. Never empties the stack."""
        self._pending.append(PopTo(target))

    def reset(self, screen: Screen) -> None:
        """Tear the whole stack down and start over. 'Quit to title' wants
        this, not replace() -- replace() swaps only the top layer and would
        leave the game screen alive and rendering underneath the title."""
        self._pending.append(Reset(screen))

    def __len__(self) -> int:
        return len(self._stack)

    @property
    def top(self) -> Screen | None:
        return self._stack[-1] if self._stack else None

    # ---- per-frame driving
    def handle_event(self, event: pygame.event.Event) -> None:
        if self._stack:
            self._stack[-1].handle_event(self, event)

    def update(self, dt: float) -> None:
        if not self._stack:
            return
        first = 0
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].blocks_update_below():
                first = i
                break
        top = len(self._stack) - 1
        # Safe to iterate: update() only queues commands.
        for i in range(first, len(self._stack)):
            self._stack[i].update(self, dt, focused=(i == top))

    def draw(self, surf: pygame.Surface) -> None:
        # Find the topmost opaque screen and start there; everything below it
        # is hidden anyway, and skipping it is free performance.
        first = 0
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].opaque():
                first = i
                break

        for screen in self._stack[first:]:  # bottom-up, so overlays land on top
            screen.draw(surf)

    def apply_pending(self) -> None:
        """The one place the stack is allowed to change shape."""
        cmds, self._pending = self._pending, []
        for cmd in cmds:
            match cmd:
                case Push(screen):
                    self._push_raw(screen, obscure_below=True)
                case Pop():
                    self._pop_raw()
                    if self._stack:
                        self._stack[-1].on_reveal()
                case Replace(screen):
                    self._pop_raw()
                    # Whatever is below was already obscured by the screen we
                    # just removed -- don't obscure it a second time.
                    self._push_raw(screen, obscure_below=False)
                case PopTo(target):
                    while len(self._stack) > 1 and not isinstance(self._stack[-1], target):
                        self._pop_raw()
                    if self._stack:
                        self._stack[-1].on_reveal()
                case Reset(screen):
                    while self._stack:
                        self._pop_raw()
                    self._push_raw(screen, obscure_below=False)

    def _push_raw(self, screen: Screen, obscure_below: bool) -> None:
        if obscure_below and self._stack:
            self._stack[-1].on_obscure()
        self._stack.append(screen)
        screen.on_enter(self)

    def _pop_raw(self) -> None:
        # on_exit only. The caller fires on_reveal once at the end, so a
        # multi-level unwind doesn't wake screens it is merely passing.
        if self._stack:
            self._stack.pop().on_exit()


# ---------------------------------------------------------------- draw helpers
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


# --------------------------------------------------------------------- screens
class TitleScreen(Screen):
    def __init__(self) -> None:
        self.menu = Menu(["New Game", "Options", "Quit"])

    def on_enter(self, stack):
        log("Title.on_enter")

    def on_exit(self):
        log("Title.on_exit")

    def on_obscure(self):
        log("Title.on_obscure")

    def on_reveal(self):
        log("Title.on_reveal")

    def handle_event(self, stack, event):
        match self.menu.handle_event(event):
            case 0:
                stack.replace(GameScreen())
            case 1:
                stack.push(OptionsMenu())
            case 2:
                stack.pop()  # empties the stack -> main loop exits

    def update(self, stack, dt, focused):
        pass

    def draw(self, surf):
        surf.fill((18, 20, 34))
        self.menu.draw(surf, "MY GAME", 80, 120)


class GameScreen(Screen):
    NPC = pygame.Rect(520, 300, 32, 48)

    def __init__(self) -> None:
        self.player = pygame.Rect(160, 300, 32, 48)
        self.clock_s = 0.0  # stand-in for the sim; freezes while paused

    def on_enter(self, stack):
        log("Game.on_enter")

    def on_exit(self):
        log("Game.on_exit")

    def on_obscure(self):
        log("Game.on_obscure")

    def on_reveal(self):
        log("Game.on_reveal")

    def _near_npc(self) -> bool:
        return self.player.inflate(48, 48).colliderect(self.NPC)

    def handle_event(self, stack, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            stack.push(PauseMenu())
        elif event.key == pygame.K_SPACE and self._near_npc():
            stack.push(
                DialogScreen(
                    "OLD MAN",
                    [
                        "You look like someone who has been debugging a render "
                        "function for three days straight.",
                        "Take this screen stack. It is dangerous to go alone.",
                    ],
                )
            )

    def update(self, stack, dt, focused):
        self.clock_s += dt
        if not focused:
            return  # held-key polling ignores focus, so guard it explicitly
        keys = pygame.key.get_pressed()
        speed = 240 * dt
        self.player.x += int((keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed)
        self.player.y += int((keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed)
        self.player.clamp_ip(surface_rect())

    def draw(self, surf):
        surf.fill((22, 44, 30))
        pygame.draw.rect(surf, (90, 130, 90), (0, 420, WIDTH, HEIGHT - 420))
        pygame.draw.rect(surf, (200, 170, 110), self.NPC)
        pygame.draw.rect(surf, (110, 180, 235), self.player)
        text(surf, f"world clock {self.clock_s:6.2f}s", 24, 24, 22, (235, 235, 245))
        text(surf, "ESC pause    arrows move", 24, 52, 18, (150, 160, 150))
        if self._near_npc():
            text(surf, "SPACE to talk", self.NPC.x - 30, self.NPC.y - 30, 18, (250, 220, 90))


class PauseMenu(Screen):
    def __init__(self) -> None:
        self.menu = Menu(["Resume", "Options", "Quit to Title"])

    def on_enter(self, stack):
        log("Pause.on_enter")

    def on_exit(self):
        log("Pause.on_exit")

    def opaque(self) -> bool:
        return False  # the frozen world shows through

    def handle_event(self, stack, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            stack.pop()
            return
        match self.menu.handle_event(event):
            case 0:
                stack.pop()
            case 1:
                stack.push(OptionsMenu())
            case 2:
                # reset, not replace: the game screen below must die too.
                stack.reset(TitleScreen())

    def update(self, stack, dt, focused):
        pass

    def draw(self, surf):
        dim(surf, 165)
        self.menu.draw(surf, "PAUSED", 80, 120)


class OptionsMenu(Screen):
    def __init__(self) -> None:
        self.menu = Menu(["Audio >", "Back"])

    def on_enter(self, stack):
        log("Options.on_enter")

    def on_exit(self):
        log("Options.on_exit")

    def opaque(self) -> bool:
        return False

    def handle_event(self, stack, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            stack.pop()
            return
        match self.menu.handle_event(event):
            case 0:
                stack.push(AudioMenu())
            case 1:
                stack.pop()

    def update(self, stack, dt, focused):
        pass

    def draw(self, surf):
        dim(surf, 215)
        self.menu.draw(surf, "OPTIONS", 80, 120)


class AudioMenu(Screen):
    def __init__(self) -> None:
        self.menu = Menu(["Back", "Back to Game"])

    def on_enter(self, stack):
        log("Audio.on_enter")

    def on_exit(self):
        log("Audio.on_exit")

    def opaque(self) -> bool:
        return False

    def handle_event(self, stack, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            stack.pop()
            return
        match self.menu.handle_event(event):
            case 0:
                stack.pop()
            # Two levels of unwind in one command; a no-op from the title path.
            case 1:
                stack.pop_to(GameScreen)

    def update(self, stack, dt, focused):
        pass

    def draw(self, surf):
        dim(surf, 235)
        self.menu.draw(surf, "AUDIO", 80, 120)


@dataclass
class DialogScreen(Screen):
    """Typewriter text box. First keypress reveals the line, second advances."""

    speaker: str
    lines: list[str]
    chars_per_sec: float = 45.0
    index: int = 0
    revealed: float = 0.0
    _wrapped: list[str] = field(default_factory=list)

    BOX = pygame.Rect(40, HEIGHT - 190, WIDTH - 80, 150)

    def on_enter(self, stack):
        log("Dialog.on_enter")
        self._wrap()

    def on_exit(self):
        log("Dialog.on_exit")

    def opaque(self) -> bool:
        return False  # the world stays visible behind the box

    def _wrap(self) -> None:
        self._wrapped = textwrap.wrap(self.lines[self.index], width=52)
        self.revealed = 0.0

    def _full_len(self) -> int:
        return sum(len(line) for line in self._wrapped)

    def handle_event(self, stack, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key not in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            return
        if self.revealed < self._full_len():
            self.revealed = float(self._full_len())  # impatient player: snap it
        elif self.index + 1 < len(self.lines):
            self.index += 1
            self._wrap()
        else:
            stack.pop()

    def update(self, stack, dt, focused):
        if focused:
            self.revealed = min(self.revealed + self.chars_per_sec * dt, self._full_len())

    def draw(self, surf):
        pygame.draw.rect(surf, (12, 14, 26), self.BOX, border_radius=8)
        pygame.draw.rect(surf, (200, 200, 220), self.BOX, width=2, border_radius=8)
        text(surf, self.speaker, self.BOX.x + 16, self.BOX.y + 10, 20, (250, 220, 90))

        budget = int(self.revealed)
        y = self.BOX.y + 44
        for line in self._wrapped:
            if budget <= 0:
                break
            text(surf, line[:budget], self.BOX.x + 16, y, 22, (235, 235, 245))
            budget -= len(line)
            y += 28

        if self.revealed >= self._full_len():
            hint = "SPACE" if self.index + 1 < len(self.lines) else "SPACE to close"
            text(surf, hint, self.BOX.right - 150, self.BOX.bottom - 30, 18, (150, 150, 165))


def surface_rect() -> pygame.Rect:
    return pygame.Rect(0, 0, WIDTH, HEIGHT)


def draw_log(surf: pygame.Surface) -> None:
    y = HEIGHT - 20 - len(EVENT_LOG) * 18
    for line in EVENT_LOG:
        text(surf, line, WIDTH - 250, y, 15, (120, 120, 140))
        y += 18


# ------------------------------------------------------------------------ main
def main() -> None:
    pygame.init()
    surf = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("screen stack")
    clock = pygame.time.Clock()

    stack = ScreenStack()
    stack.push(TitleScreen())
    stack.apply_pending()

    running = True
    while running and len(stack):
        dt = clock.tick(60) / 1000.0
        # Drain the queue exactly once, here. Calling event.get() anywhere else
        # steals events from whoever calls it next.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                stack.handle_event(event)

        stack.update(dt)
        stack.apply_pending()

        surf.fill((0, 0, 0))
        stack.draw(surf)
        draw_log(surf)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()