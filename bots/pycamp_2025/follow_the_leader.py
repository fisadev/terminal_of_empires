import random
import json
import os
import fcntl
from time import time
from datetime import datetime

from game import CASTLE, CONQUER, HARVEST, MINE, Position

MESSAGE_FILE = "/tmp/message_channel.json"
HOLA_MESSAGE = "hola"
LEADER_MESSAGE = "LEADER"


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


class BotLogic:
    """
    Bot logic for the FOLLOW THE LEADER bot.

    The first player is designated as the leader, and all bots of the same type do not attack each other.
    """

    def __init__(self):
        self.id = str(time()).replace(".", "")
        self.msg_id = 0
        self.partners = {}
        self.castle = None
        self.cooperate = True
        self._initialize_channel()
        self._write_message(HOLA_MESSAGE)

    def _initialize_channel(self):
        if os.path.exists(MESSAGE_FILE):
            creation_time = os.path.getctime(MESSAGE_FILE)
            if (
                datetime.now() - datetime.fromtimestamp(creation_time)
            ).total_seconds() > 60:
                os.remove(MESSAGE_FILE)

        if not os.path.exists(MESSAGE_FILE):
            with open(MESSAGE_FILE, "w") as f:
                json.dump([], f)
            self._write_message(LEADER_MESSAGE)

    def _write_message(self, content):
        self.msg_id += 1
        with open(MESSAGE_FILE, "r+") as f:
            messages = json.load(f)
            messages.append({"id": self.id, "msg_id": self.msg_id, "content": content})
            f.seek(0)
            json.dump(messages, f)
            f.truncate()

    def _read_messages(self, offset=0):
        with open(MESSAGE_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            messages = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
        return [msg for msg in messages if msg["msg_id"] > offset]

    def _public_castle(self, castle):
        self._write_message(f"{CASTLE} {castle.x} {castle.y}")

    def _get_leader(self):
        messages = self._read_messages()

        leaders = (
            msg["id"] for msg in messages if msg["content"].startswith(LEADER_MESSAGE)
        )
        return next(reversed(list(leaders)), None)

    def _update_partners(self, world):
        messages = self._read_messages()
        all_partners = [msg["id"] for msg in messages if msg["content"] == HOLA_MESSAGE]
        for partner in all_partners:
            if partner not in self.partners:
                self.partners[partner] = {CASTLE: None, "name": None}

            if self.partners[partner][CASTLE] is None:
                castle = [
                    msg
                    for msg in messages
                    if msg["id"] == partner and msg["content"].startswith(CASTLE)
                ]
                if castle:
                    castle = castle[0]["content"].split(" ")
                    castle_pos = Position(int(castle[1]), int(castle[2]))
                    self.partners[partner] = {
                        CASTLE: castle_pos,
                        "name": world.get(castle_pos).owner,
                    }

    def turn(self, map_size, my_resources, world):
        if self.castle is None:
            self.castle = next(
                (
                    position
                    for position, terrain in world.items()
                    if terrain.owner == MINE and terrain.structure == CASTLE
                ),
                None,
            )
            self._public_castle(self.castle)
            return HARVEST, None

        partners_names = [MINE]
        current_players = list(set([terrain.owner for _, terrain in world.items()]))
        if self.cooperate:
            self._update_partners(world)
            partners_names = [
                partner["name"] for partner in self.partners.values() if partner["name"]
            ]
            enemies = [
                player
                for player in current_players
                if player not in [None, *partners_names]
            ]
        else:
            leader = self._get_leader()
            leader_is_alive = self.partners[leader]["name"] in current_players
            if not leader_is_alive:
                self._write_message(LEADER_MESSAGE)
                leader = self.id

            if leader != self.id and leader_is_alive:
                return HARVEST, None
            enemies = [player for player in current_players if player != MINE]

        if len(enemies) == 0:
            self.cooperate = False

        my_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner == MINE
        ]

        conquerable_enemy_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner in enemies
            and any(is_adjacent(position, my_position) for my_position in my_terrain)
        ]

        if conquerable_enemy_terrain:
            # keep the resources high so we can conquer anything we want
            if my_resources < 100:
                return HARVEST, None
            return CONQUER, random.choice(conquerable_enemy_terrain)

        # if no enemy terrain, then try to conquer neutral terrain
        conquerable_neutral_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner is None
            and any(is_adjacent(position, my_position) for my_position in my_terrain)
        ]

        if conquerable_neutral_terrain:
            if my_resources < 1:
                return HARVEST, None
            return CONQUER, random.choice(conquerable_neutral_terrain)

        return HARVEST, None
