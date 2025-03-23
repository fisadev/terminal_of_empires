import sys

import click

from game import ToE
from ui import ToEUI


@click.command()
@click.option("--width", type=int, default=40, help="The width of the map.")
@click.option("--height", type=int, default=20, help="The height of the map.")
@click.option("--players", type=str, help="Players, specified as a comma separated list of player_name:bot_type (or optionally with the initial position as player_name:bot_type:x.y) .")
@click.option("--no-ui", is_flag=True, help="Don't show the ui, just run the game until the end and inform the winner.")
@click.option("--ui-turn-delay", type=float, default=0.2, help="Seconds to wait between turns when showing the ui.")
@click.option("--turn-timeout", type=float, default=0.5, help="Maximum seconds a player can take to think its turn.")
@click.option("--log-path", type=click.Path(), default="./toe.log", help="Path for the log file of the game.")
@click.option("--max-turns", type=int, default=None, help="Maximum number of turns to play (no limit if not specified).")
@click.option("--debug", is_flag=True, help="In debug mode, any errors in the bot will stop the game and the traceback will be shown.")
def main(width, height, players, no_ui, ui_turn_delay, log_path, turn_timeout, max_turns, debug):
    """
    Run a game of Terminal of Empires.
    """
    if no_ui:
        ui = None
    else:
        ui = ToEUI(ui_turn_delay)

    toe = ToE(width, height, ui=ui, log_path=log_path, turn_timeout=turn_timeout, debug=debug)

    for player_info in players.split(","):
        try:
            parts = player_info.split(":")
            if len(parts) == 2:
                name, bot_type = player_info.split(":")
                castle_position = None
            elif len(parts) == 3:
                name, bot_type, position = player_info.split(":")
                x, y = position.split(".")
                castle_position = (int(x), int(y))
            else:
                raise ValueError()

            bot_type = bot_type.lower()
        except ValueError:
            print(f"Invalid player info: {player_info}. Should be name:bot_type")
            sys.exit(1)

        toe.add_player(name, bot_type, castle_position=castle_position)

    if ui:
        with ui.show():
            result = toe.play(max_turns=max_turns)
    else:
        result = toe.play(max_turns=max_turns)

    if result:
        winners, turns_played = result
        print(" and ".join(p.name for p in winners), "won in", turns_played, "turns!")


if __name__ == '__main__':
    main()
