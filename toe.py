import sys
from collections import defaultdict

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
@click.option("--repeat", type=int, default=1, help="Repeat the game N times and return stats about winners of the games.")
def main(width, height, players, no_ui, ui_turn_delay, log_path, turn_timeout, max_turns, debug, repeat):
    """
    Run a game of Terminal of Empires.

    Optionally, repeat the game N times and return stats about winners of the games.
    """
    scoreboard = defaultdict(int)
    for game_number in range(repeat):
        if no_ui:
            print(f"Starting game {game_number + 1} of {repeat}...")
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
            print("Game", game_number + 1, "ended in", turns_played, "turns!")
            print("Winners:", ",".join(player.name for player in winners))
            score = 1 / len(winners)
            for winner in winners:
                scoreboard[winner.name] += score
            print()

    if repeat > 1:
        print("Final scoreboard of", repeat, "games:")
        for player, score in sorted(scoreboard.items(), key=lambda x: x[1], reverse=True):
            print(f"{player}: {score}")


if __name__ == '__main__':
    main()
