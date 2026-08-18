from dataclasses import dataclass

import agent
from player_controller import PlayerController
from world import World, find_spawn
from agent import Agent

@dataclass
class Level:
    world: World
    agents: list[Agent]
    player: Agent

    @classmethod
    def from_tmx(cls, tmx) -> "Level":
        world = World.from_tmx(tmx)
        spawn = find_spawn(tmx)
        player = Agent(*spawn, kind="wizard", controller=PlayerController())

        return cls(world=world, agents=[player], player=player)
