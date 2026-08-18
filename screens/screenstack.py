from screens.screen import Screen
from dataclasses import dataclass
import pygame

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
    def __init__(self):
        self._stack: list[Screen] = []
        self._pending: list[Command] = []

    def push(self, screen: Screen) -> None:
        self._pending.append(Push(screen))

    def pop(self) -> None:
        self._pending.append(Pop())

    def replace(self, screen: Screen) -> None:
        self._pending.append(Replace(screen))

    def pop_to(self, target: type) -> None:
        self._pending.append(PopTo(target))

    def reset(self, screen: Screen) -> None:
        self._pending.append(Reset(screen))

    def __len__(self) -> int:
        return len(self._stack)

    def top(self) -> Screen | None:
        return self._stack[-1] if self._stack else None

    def handle_event(self, event: pygame.Event) -> None:
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

        for i in range(first, len(self._stack)):
            self._stack[i].update(self, dt, focused=i==top)

    def draw(self, surf: pygame.Surface) -> None:
        if not self._stack:
            return
        first = 0
        for i in range(len(self._stack) -1, -1, -1):
            if self._stack[i].opaque():
                first = i
                break

        for screen in self._stack[first:]:
            screen.draw(surf)

    def apply_pending(self) -> None:
        cmds, self._pending = self._pending, []
        for cmd in cmds:
            match cmd:
                case Push(screen):
                    self.push_raw(screen, True)
                case Pop():
                    self.pop_raw()
                    if self._stack:
                        self._stack[-1].on_reveal()
                case Replace(screen):
                    self.pop_raw()
                    self.push_raw(screen, False)
                case PopTo(target):
                    while len(self._stack) > 1 and not isinstance(self._stack[-1], target):
                        self.pop_raw()
                    if self._stack:
                        self._stack[-1].on_reveal()
                case Reset(screen):
                    while self._stack:
                        self.pop_raw()
                    self.push_raw(screen, True)

    def push_raw(self, screen: Screen, obscure_below: bool):
        if obscure_below and self._stack:
            self._stack[-1].on_obscure()
        self._stack.append(screen)
        screen.on_enter(self)

    def pop_raw(self):
        if self._stack:
            self._stack.pop().on_exit()
