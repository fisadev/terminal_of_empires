from contextlib import contextmanager
from time import sleep
import curses

from blessings import Terminal
from game import FARM, FORT, CASTLE, LAND, Position


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
        self.last_args = None

    def add_player(self, player):
        """
        Register a player in the ui.
        """
        if not self.free_colors:
            self.free_colors = [
                self.term.blue, self.term.red, self.term.green, self.term.yellow, self.term.cyan, self.term.white, self.term.magenta,
            ]

        self.player_colors[player.name] = self.free_colors.pop(0)

    def render(self, toe, turn_number, winners=None, running_in_fullscreen=True):
        """
        Render the game state.
        """
        self.last_args = (toe, turn_number, winners)

        if winners:
            winner_names = {winner.name for winner in winners}
        else:
            winner_names = set()

        if running_in_fullscreen:
            print(self.term.move(0, 0))

        self.render_world(toe, winner_names, blink_winners=False)
        self.render_players_status(toe, turn_number, winner_names, blink_winners=False)

        if winner_names and running_in_fullscreen:
            blink = True
            while True:
                sleep(0.3)
                print(self.term.move(0, 0))
                self.render_world(toe, winner_names, blink_winners=blink)
                self.render_players_status(toe, turn_number, winner_names, blink_winners=blink)
                blink = not blink

        sleep(self.turn_delay)

    def render_world(self, toe, winner_names, blink_winners=False):
        """
        Render the world of the game.
        """
        for y in range(toe.map_size.y):
            row = ""
            for x in range(toe.map_size.x):
                terrain = toe.world[Position(x, y)]
                if blink_winners and terrain.owner in winner_names:
                    row += f"{self.player_colors[None]}{ICONS[terrain.structure]}{self.term.normal}"
                else:
                    row += f"{self.player_colors[terrain.owner]}{ICONS[terrain.structure]}{self.term.normal}"
            print(row)

    def render_players_status(self, toe, turn_number, winner_names, blink_winners=False, running_in_fullscreen=True):
        """
        Render the status of the players.
        """
        print("Turn", turn_number, "| Stats:", self.term.clear_eol)
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
                f"{player_stats[player.name]['tiles']}t "
                f"{percent}%"
                f"{self.term.clear_eol}"
            )

            if player.alive:
                if player.name in winner_names:
                    if blink_winners:
                        print(f"{self.player_colors[None]}{player}: {stats} WINNER!!{self.term.normal} Press ctrl-c to quit{self.term.clear_eol}")
                    else:
                        print(f"{self.player_colors[player.name]}{player}: {stats} WINNER!!{self.term.normal} Press ctrl-c to quit{self.term.clear_eol}")
                else:
                    print(f"{self.player_colors[player.name]}{player}: {stats}{self.term.normal}{self.term.clear_eol}")
            else:
                print(f"{self.player_colors[player.name]}{player}: {stats} DEAD{self.term.normal}{self.term.clear_eol}")

    @contextmanager
    def show(self):
        """
        Context manager to wrap the showing of the game ui during its execution.
        """
        try:
            with self.term.fullscreen(), self.term.hidden_cursor():
                print(self.term.clear)
                yield self
        finally:
            print(self.term.normal)
            if self.last_args is not None:
                self.render(*self.last_args, running_in_fullscreen=False)
