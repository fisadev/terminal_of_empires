from contextlib import contextmanager
from time import sleep

from blessings import Terminal
from game import FARM, FORT, CASTLE, LAND


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
        self.render_world(toe, winner, blink_winner=False)
        self.render_players_status(toe, turn_number, winner, blink_winner=False)

        if winner:
            blink = True
            while True:
                sleep(0.3)
                self.render_world(toe, winner, blink_winner=blink)
                self.render_players_status(toe, turn_number, winner, blink_winner=blink)
                blink = not blink


        sleep(self.turn_delay)

    def render_world(self, toe, winner, blink_winner=False):
        """
        Render the world of the game.
        """
        for position, terrain in toe.world.items():
            with self.term.location(position.x * 2, position.y):
                if winner and blink_winner and terrain.owner == winner.name:
                    print(f"{self.player_colors[None]}{ICONS[terrain.structure]}{self.term.normal}", end="")
                else:
                    print(f"{self.player_colors[terrain.owner]}{ICONS[terrain.structure]}{self.term.normal}", end="")

    def render_players_status(self, toe, turn_number, winner, blink_winner=False):
        """
        Render the status of the players.
        """
        with self.term.location(0, toe.map_size.y):
            print("Turn", turn_number, "| Stats:")
            player_stats = {
                player.name: {CASTLE: 0, FARM: 0, FORT: 0, "tiles": 0}
                for player in toe.players.values()
            }

            for terrain in toe.world.values():
                if terrain.owner is not None:
                    player_stats[terrain.owner]["tiles"] += 1
                    if terrain.structure in (FARM, FORT, CASTLE):
                        player_stats[terrain.owner][terrain.structure] += 1

            total_tiles = toe.map_size.x * toe.map_size.y
            for player in toe.players.values():
                tiles = len([t for t in toe.world.values() if t.owner == player.name])
                percent = int((tiles / total_tiles) * 100)
                stats = (
                    f"{player.resources}$ "
                    f"{player_stats[player.name][CASTLE]}[] "
                    f"{player_stats[player.name][FARM]}// "
                    f"{player_stats[player.name][FORT]}<> "
                    f"{player_stats[player.name]["tiles"]}t "
                    f"{percent}%"
                )

                if player.alive:
                    if player is winner:
                        if blink_winner:
                            print(f"{self.player_colors[None]}{player}: {stats} WINNER!!{self.term.normal} Press ctrl-c to quit")
                        else:
                            print(f"{self.player_colors[player.name]}{player}: {stats} WINNER!!{self.term.normal} Press ctrl-c to quit")
                    else:
                        print(f"{self.player_colors[player.name]}{player}: {stats}{self.term.normal}     ")
                else:
                    print(f"{self.player_colors[player.name]}{player}: {stats} DEAD{self.term.normal}     ")

    @contextmanager
    def show(self):
        """
        Context manager to wrap the showing of the game ui during its execution.
        """
        with self.term.fullscreen(), self.term.hidden_cursor():
            yield self


if __name__ == "__main__":
    app = ToEUI()
    app.run()
