from intent import Intent

class PlayerController:
    def __init__(self):
        self.pending: list[Intent] = []

    def feed(self, intent):
        self.pending.append(intent)

    def update(self, agent, world):
        for intent in self.pending:
            agent.try_move(intent, world)
            self.last_move = intent
        self.pending.clear()    
