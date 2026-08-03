import enum


class Intent(enum.Enum):
    MOVE_NONE = (0, 0)
    MOVE_UP = (0, -1)
    MOVE_DOWN = (0, 1)
    MOVE_LEFT = (-1, 0)
    MOVE_RIGHT = (1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value
