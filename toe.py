import sys
import importlib

import click

from game import ToE
from ui import ToEUI


@click.command()
@click.option("--width", type=int, default=40, help="The width of the map.")
@click.option("--height", type=int, default=20, help="The height of the map.")
@click.option("--players", type=str, help="Players, specified as a comma separated list of player_name:bot_type.")
@click.option("--no-ui", is_flag=True, help="Don't show the ui, just run the game until the end and inform the winner.")
@click.option("--ui-turn-delay", type=float, default=0.2, help="Seconds to wait between turns when showing the ui.")
@click.option("--turn-timeout", type=float, default=0.5, help="Maximum seconds a player can take to think its turn.")
@click.option("--log-path", type=click.Path(), default="./toe.log", help="Path for the log file of the game.")
def main(width, height, players, no_ui, ui_turn_delay, log_path, turn_timeout):
    """
    Run a game of Terminal of Empires.
    """
    if no_ui:
        ui = None
    else:
        ui = ToEUI(ui_turn_delay)

    toe = ToE(width, height, ui=ui, log_path=log_path, turn_timeout=turn_timeout)

    for player_info in players.split(","):
        try:
            name, bot_type = player_info.split(":")
            bot_type = bot_type.lower()
        except ValueError:
            print(f"Invalid player info: {player_info}. Should be name:bot_type")
            sys.exit(1)

        toe.add_player(name, bot_type)

    if ui:
        with ui.show():
            winner, turns_played = toe.play()
    else:
        winner, turns_played = toe.play()
        print(winner, "won in", turns_played, "turns!")


if __name__ == '__main__':
    main()
