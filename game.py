import random
import importlib
import sys
import logging
from collections import namedtuple
from datetime import datetime, timedelta
from multiprocessing import Process, Manager
from time import sleep


LAND = "land"
FARM = "farm"
FORT = "fort"
CASTLE = "castle"

MINE = "mine"

CONQUER = "conquer"
HARVEST = "harvest"

STRUCTURE_COST = {
    FARM: 5,
    FORT: 25,
    CASTLE: 75,
}

VALID_ACTIONS = (CONQUER, HARVEST, FARM, FORT, CASTLE)
STRUCTURES = (FARM, FORT, CASTLE)
DEFENDER_STRUCTURES = (FORT, CASTLE)

# if a cost is a tuple, it means different costs when undefended vs defended by nearby defeder
# structure
CONQUER_COSTS = {
    LAND: (1, 25),
    FARM: (2, 25),
    FORT: 50,
    CASTLE: 100,
}

HARVEST_PRODUCTION = {
    LAND: 0,
    FARM: 5,
    FORT: 0,
    CASTLE: 5,
}

COMMS_IDLE = "idle"
COMMS_AWAITING_ACTION = "awaiting_action"
COMMS_ACTION_READY = "action_ready"
COMMS_ACTION_FAILED = "action_failed"

TILES_PER_CASTLE_LIMIT = 50

Position = namedtuple("Position", "x y")
Terrain = namedtuple("Terrain", "structure owner")


class Player:
    """
    A player playing the game.
    Its bot logic is run in a subprocess.
    """
    def __init__(self, name, bot_type, resources, debug):
        self.name = name
        self.bot_type = bot_type
        self.resources = resources
        self.debug = debug
        self.alive = True
        self.debug_bot_logic = None

        self.comms = None
        self.process = None

    def __str__(self):
        return f"{self.name}:{self.bot_type}"

    def start_bot_logic(self):
        """
        Launch the bot logic subprocess, unless the game is in debug mode, in that case just
        instantiate the bot.
        """
        if self.debug:
            self.debug_bot_logic = import_bot_logic(self.bot_type)
        else:
            self.comms = Manager().dict()
            self.comms["status"] = COMMS_IDLE
            self.process = Process(target=bot_logic_subprocess_loop, args=(self.bot_type, self.comms))
            self.process.start()

    def stop_bot_logic(self):
        """
        Stop the bot logic subprocess.
        """
        if not self.debug:
            self.process.kill()

    def ask_action(self, map_size, world, timeout):
        """
        Ask the bot logic for an action, waiting up to timeout seconds.
        """
        if self.debug:
            action = self.debug_bot_logic.turn(map_size, self.resources, world)
            return True, action
        else:
            self.comms["action_params"] = (map_size, self.resources, world)
            self.comms["status"] = COMMS_AWAITING_ACTION

            start_time = datetime.now()
            while datetime.now() - start_time < timeout:
                if self.comms["status"] == COMMS_ACTION_READY:
                    return True, self.comms["action"]
                elif self.comms["status"] == COMMS_ACTION_FAILED:
                    return False, self.comms["error"]

            return False, f"timeout, did not return an action in {timeout.total_seconds()} seconds"


def bot_logic_subprocess_loop(bot_type, comms):
    """
    The loop that runs the bot logic in a subprocess, communicating via comms.
    """
    bot_logic = import_bot_logic(bot_type)

    while True:
        if comms["status"] == COMMS_AWAITING_ACTION:
            map_size, player_resources, world = comms["action_params"]
            try:
                action = bot_logic.turn(map_size, player_resources, world)

                comms["action"] = action
                comms["status"] = COMMS_ACTION_READY
            except Exception as err:
                comms["error"] = repr(err)
                comms["status"] = COMMS_ACTION_FAILED


def import_bot_logic(bot_type):
    """
    Try to import the bot logic module and instantiate its BotLogic class.
    """
    try:
        bot_module = importlib.import_module("bots." + bot_type)
    except ImportError:
        print(f"Could not import bot module named {bot_type}.")
        print(f"Are you sure there's a bots/{bot_type}.py file and it's a valid python module?")
        sys.exit(1)

    try:
        bot_class = getattr(bot_module, "BotLogic")
    except AttributeError:
        print(f"Could not find BotLogic class in bot module named {bot_type}.")
        print(f"Are you sure there's a BotLogic class defined in bots/{bot_type}.py?")
        sys.exit(1)

    return bot_class()


class ToE:
    """
    A game of Terrain of Empires.
    """
    def __init__(self, width, height, ui=None, log_path=None, turn_timeout=0.5, debug=False):
        self.map_size = Position(width, height)
        self.ui = ui
        self.turn_timeout = timedelta(seconds=turn_timeout)
        self.debug = debug

        self.players = {}
        self.players_comms = {}
        self.world = {
            Position(x, y): Terrain(LAND, None)
            for x in range(self.map_size.x)
            for y in range(self.map_size.y)
        }

        if log_path is None:
            log_path = "./toe.log"

        logging.basicConfig(
            filename=log_path, level=logging.INFO, filemode="w",
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logging.info("game created with size %s x %s", width, height)

    def add_player(self, name, bot_type, castle_position=None):
        """
        Add a player to the map. If no castle position is specified, choose one at random.
        """
        if castle_position is None:
            # keep trying until we find an empty spot for the new player
            while True:
                castle_position = Position(
                    random.randint(0, self.map_size.x - 1),
                    random.randint(0, self.map_size.y - 1),
                )
                if self.world[castle_position].structure == LAND:
                    break

        player = Player(name, bot_type, resources=0, debug=self.debug)

        self.players[name] = player
        self.world[castle_position] = Terrain(CASTLE, name)

        if self.ui:
            self.ui.add_player(player)

        logging.info("player %s added with initial castle at %s", player, castle_position)

    def play(self, max_turns=None):
        """
        Play the game until one player has conquered all other players, or until the maximum number
        of turns is reached.
        Return the winner and the number of turns played.
        """
        logging.info("starting game loop")

        logging.info("starting the subprocesses for the player bots logic")
        for player in self.players.values():
            player.start_bot_logic()

        turn_number = 1
        while max_turns is None or turn_number < max_turns:
            players = list(self.players.values())
            random.shuffle(players)
            logging.info("turn %s order: %s", turn_number, ",".join(p.name for p in players))

            for player in players:
                if not player.alive:
                    # dead players don't play anymore
                    continue

                turn_ok, reason = self.run_player_turn(player)
                if turn_ok:
                    logging.info("%s action ran ok: %s", player, reason)
                else:
                    logging.info("%s action failed: %s", player, reason)

            if self.ui:
                self.ui.render(self, turn_number)

            winner = self.get_winner()
            if winner:
                break

            turn_number += 1

        if winner:
            winners = [winner]
        else:
            # it's a tie! all alive players won
            winners = [player for player in self.players.values() if player.alive]

        for player in self.players.values():
            player.stop_bot_logic()

        if self.ui:
            self.ui.render(self, turn_number, winners)

        return winners, turn_number

    def run_player_turn(self, player):
        """
        A player takes its turn to play.
        """
        player_world = self.copy_world_for_player(player)

        logging.info("%s calling turn() function with %s resources", player, player.resources)
        got_action, action = player.ask_action(
            self.map_size,
            player_world,
            timeout=self.turn_timeout,
        )

        if got_action:
            logging.info("%s requested action: %s", player, action)
        else:
            return False, action

        if not isinstance(action, (list, tuple)) or not len(action) == 2:
            return False, f"{action} does not follow the action format, (action_type, position)"

        action_type, action_position = action

        if action_type not in VALID_ACTIONS:
            return False, f"unknown action type {action_type}"

        if action_type == CONQUER:
            return self.conquer(player, action_position)
        elif action_type == HARVEST:
            return self.harvest(player)
        else:
            assert action_type in STRUCTURES
            return self.build(player, action_type, action_position)

    def copy_world_for_player(self, player):
        """
        Return a copy of the world to pass to the player (for safety), also modifying the world so
        their terrain positions have "mine" as owner.
        """
        return {
            position: Terrain(
                terrain.structure,
                terrain.owner if terrain.owner != player.name else MINE,
            )
            for position, terrain in self.world.items()
        }

    def harvest(self, player):
        """
        Produce resources with the player's structures.
        """
        produced_resources = 0

        for terrain in self.world.values():
            if terrain.owner == player.name:
                produced_resources += HARVEST_PRODUCTION[terrain.structure]

        player.resources += produced_resources

        return True, f"harvest produced {produced_resources} resources"

    def conquer(self, player, position):
        """
        Conquer a position on the map, if possible. Return True if the action was successful.
        """
        if position not in self.world:
            return False, f"can't conquer a position that isn't on the map {position}"

        target = self.world[position]
        if target.owner == player.name:
            return False, "can't conquer terrain that is already yours"

        adjacents = [
            self.world[adjacent_position]
            for adjacent_position in self.adjacent_positions(position)
        ]

        in_range = any(
            adjacent.owner == player.name
            for adjacent in adjacents
        )
        if not in_range:
            return False, "can't conquer terrain that isn't adjacent to your empire"

        cost = CONQUER_COSTS[target.structure]
        thing_conquered = target.structure

        if isinstance(cost, tuple):
            undefended_cost, defended_cost = cost

            is_defended = any(
                adjacent.structure in DEFENDER_STRUCTURES and adjacent.owner == target.owner
                for adjacent in adjacents
            )
            if is_defended:
                cost = defended_cost
                thing_conquered = f"defended {thing_conquered}"
            else:
                cost = undefended_cost
                thing_conquered = f"unprotected {thing_conquered}"

        if player.resources < cost:
            return False, f"not enough resources to conquer {thing_conquered}, costs {cost}"

        self.world[position] = Terrain(LAND, player.name)
        player.resources -= cost

        enemy = target.owner
        if enemy is None:
            enemy = "neutral"

        return True, f"conquered {thing_conquered} from {enemy} spending {cost} resources"

    def build(self, player, structure, position):
        """
        Fortify a position on the map, if possible. Return True if the action was successful.
        """
        cost = STRUCTURE_COST[structure]

        if player.resources < cost:
            return False, f"not enough resources to build {structure}, costs {cost}"

        if position not in self.world:
            return False, f"can't conquer a position that isn't on the map {position}"

        if self.world[position].owner != player.name:
            return False, "can't build structures on terrain that you don't own"

        if structure == CASTLE:
            owned_castles = 0
            owned_tiles = 0
            for terrain in self.world.values():
                if terrain.owner == player.name and terrain.structure == CASTLE:
                    owned_castles += 1
                if terrain.owner == player.name:
                    owned_tiles += 1

            if owned_castles and owned_tiles / owned_castles <= TILES_PER_CASTLE_LIMIT:
                return False, f"can't build more castles, you need more tiles (you have {owned_castles} castles and {owned_tiles} tiles)"

        self.world[position] = Terrain(structure, player.name)
        player.resources -= cost
        return True, f"built {structure} spending {cost} resources"

    def adjacent_positions(self, position):
        """
        Return the valid positions adjacent to the given position, considering the map size.
        """
        x, y = position
        candidates = [
            Position(x - 1, y),
            Position(x + 1, y),
            Position(x, y - 1),
            Position(x, y + 1),
        ]
        return [
            candidate
            for candidate in candidates
            if candidate in self.world
        ]

    def get_winner(self):
        """
        Return the winner if there is one, or None if the game is still ongoing. Mark dead players
        as dead.
        """
        # who has castles?
        players_with_castles = set()
        for terrain in self.world.values():
            if terrain.owner and terrain.structure == CASTLE:
                players_with_castles.add(terrain.owner)

        # update alive/dead statuses
        for player in self.players.values():
            was_alive = player.alive
            still_alive = player.name in players_with_castles
            player.alive = still_alive

            if was_alive and not still_alive:
                logging.info("%s died! It no longer has castles", player)

        if len(players_with_castles) == 1:
            winner = self.players[players_with_castles.pop()]
            logging.info("%s won!", winner)
            return winner
