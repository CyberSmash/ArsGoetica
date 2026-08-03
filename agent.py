import dataclasses

from intent import Intent
from world import World
from typing import Protocol

# This avoids needing an ABC. The Protocol defines the structure,
# and since we assign a PlayerController to our player agent,
# which satisfies this structure the type system  can resolve it.
class Controller(Protocol):
    def feed(self, intent: Intent): ...
    def update(self, intent: Intent): ...
    def get_last_move(self) -> tuple[int, int]: ...

@dataclasses.dataclass
class Agent:
    x: int
    y: int
    kind: str = "player"
    facing: Intent = Intent.MOVE_DOWN
    controller: "Controller | None" = None

    def try_move(self, intent: Intent, world: World) -> bool:
        if intent is not Intent.MOVE_NONE:
            self.facing = intent
        
        dx, dy = intent.delta
        tx, ty = self.x + dx, self.y + dy
        if world.is_passable(tx, ty):
            self.x, self.y = tx, ty
            return True
        return False

    def get_action_cell(self):
        dx, dy = self.facing.delta
        return (self.x + dx, self.y + dy)
