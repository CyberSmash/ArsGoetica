from screens.screenstack import ScreenStack

def quit_to_title(stack: ScreenStack):
    from screens.titlescreen import TitleScreen
    return stack.reset(TitleScreen())

def to_game(stack: ScreenStack):
    from screens.gamescreen import GameScreen
    return stack.replace(GameScreen())

def open_pause(stack: ScreenStack): ...

def open_cast(stack: ScreenStack):
    from screens.spellcast import SpellCast
    return stack.push(SpellCast())

def open_dialog(stack: ScreenStack): ...

