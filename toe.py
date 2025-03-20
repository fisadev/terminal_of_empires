import sys
import importlib

import click

from game import ToE
from ui import ToEUI


def import_bot_logic(bot_type):
    """
    Try to import the bot logic module and instantiate its BotLogic class.
    """
    try:
        bot_module = importlib.import_module("bots." + bot_type)
    except ImportError:
        print(f"Could not import bot module named {bot_type}.")
        print("Are you sure there's a bots/{bot_type}.py file and it's a valid python module?")
        sys.exit(1)

    try:
        bot_class = getattr(bot_module, "BotLogic")
    except AttributeError:
        print(f"Could not find BotLogic class in bot module named {bot_type}.")
        print("Are you sure there's a BotLogic class defined in bots/{bot_type}.py?")
        sys.exit(1)

    return bot_class()


@click.command()
@click.option("--width", type=int, default=40, help="The width of the map.")
@click.option("--height", type=int, default=20, help="The height of the map.")
@click.option("--players", type=str, help="Players, specified as a comma separated list of player_name:bot_type.")
@click.option("--no-ui", is_flag=True, help="Don't show the ui, just run the game until the end and inform the winner.")
@click.option("--ui-turn-delay", type=float, default=0.2, help="Seconds to wait between turns when showing the ui.")
def main(width, height, players, no_ui, ui_turn_delay):
    """
    Run a game of Terminal of Empires.
    """
    if no_ui:
        ui = None
    else:
        ui = ToEUI(ui_turn_delay)

    toe = ToE(width, height, ui=ui)

    # TODO allow name:bot_type:castle_position
    for player_info in players.split(","):
        try:
            name, bot_type = player_info.split(":")
            bot_type = bot_type.lower()
        except ValueError:
            print(f"Invalid player info: {player_info}. Should be name:bot_type")
            sys.exit(1)

        bot_logic = import_bot_logic(bot_type)
        toe.add_player(name, bot_logic)

    with ui.show():
        winner, turns_played = toe.play()

    if not ui:
        print(winner, "won in", turns_played, "turns!")


if __name__ == '__main__':
    main()
