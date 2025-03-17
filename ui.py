import sys
from time import sleep

from blessings import Terminal
from game import Position, FARM, FORT, CASTLE, LAND


ICONS = {
    LAND: "::",
    FARM: "//",
    FORT: "<>",
    CASTLE: "[]",
}


class ToEUI:
    """
    Cli UI for Terminal of Empires.
    """
    def __init__(self, turn_delay):
        self.term = Terminal()
        self.turn_delay = turn_delay
        self.free_colors = None
        self.player_colors = {None: self.term.black}

    def add_player(self, player):
        """
        Register a player in the ui.
        """
        if not self.free_colors:
            self.free_colors = [
                self.term.blue, self.term.red, self.term.green, self.term.yellow, self.term.cyan, self.term.white, self.term.magenta,
            ]

        self.player_colors[player.name] = self.free_colors.pop(0)

    def render(self, toe, turn_number, winner):
        """
        Render the game state.
        """
        with self.term.fullscreen():
            for position, terrain in toe.world.items():
                with self.term.location(position.x * 2, position.y):
                    print(f"{self.player_colors[terrain.owner]}{ICONS[terrain.structure]}{self.term.normal}", end="")

            with self.term.location(0, toe.map_size.y):
                print("Turn", turn_number, "| Resources:")
                for player in toe.players.values():
                    if player.alive:
                        if player is winner:
                            print(f"{self.player_colors[player.name]}{player}: WINNER!!{self.term.normal}")
                        else:
                            print(f"{self.player_colors[player.name]}{player}: {player.resources}{self.term.normal}")
                    else:
                        print(f"{self.player_colors[player.name]}{player}: DEAD{self.term.normal}")

                if winner:
                    print("Press ctrl-c to quit")
                    sleep(99999999)

        sleep(self.turn_delay)


if __name__ == "__main__":
    app = ToEUI()
    app.run()
