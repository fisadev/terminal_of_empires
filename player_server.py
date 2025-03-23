import logging

import click
import psutil
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from game import Player
from serialization_helpers import deserialize_map_size, deserialize_world

logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s",
)

app = FastAPI()

player_bot = None


class TurnRequest(BaseModel):
    map_size: tuple
    world: dict
    resources: int


def _print_ips():
    try:
        addrs = psutil.net_if_addrs()

        for k, v in addrs.items():
            if k.startswith("br"):
                continue
            if k.startswith("docker"):
                continue
            if k.startswith("lo"):
                continue

            for item in v:
                if item.family == 2:
                    ip = item.address
                    logging.info(f"IP: {ip}")
    except Exception as e:
        logging.error(f"Error: {e}")


@app.post("/turn")
def turn(body: TurnRequest):
    map_size = deserialize_map_size(body.map_size)
    world = deserialize_world(body.world)

    player_bot.resources = body.resources
    action_committed, action = player_bot.ask_action(
        map_size=map_size, world=world, timeout=None
    )

    if action_committed:
        return dict(action=action)

    raise HTTPException(status_code=404, detail="Failed to commit action")


@click.command()
@click.option(
    "--player",
    type=str,
    help="Player, specified as player_name:bot_type",
)
def main(player):
    global player_bot


    _print_ips()

    name, bot_type = player.split(":")

    print(f"Player: {name}, Bot Type: {bot_type}")

    player_bot = Player(name=name, bot_type=bot_type, debug=True)
    player_bot.start_bot_logic()

    uvicorn.run(app=app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
