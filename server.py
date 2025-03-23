import json
import logging
import psutil

import uvicorn
from fastapi import FastAPI

from game import Player

logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s",
)

app = FastAPI()


def print_ips():
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
def turn(map_size, resources, world):
    player.resources = resources
    action = player.ask_action(map_size=map_size, world=world, timeout=None)

    return json.dumps(action)


if __name__ == "__main__":
    print_ips()

    player = Player("server", "aggressive", resources=0, debug=True)
    player.start_bot_logic()

    uvicorn.run(app=app, host="0.0.0.0", port=8000)
