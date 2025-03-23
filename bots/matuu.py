import math
from collections import Counter
import os
import logging

from game import Position, Terrain


# only log if DEBUG is true
if os.environ.get("DEBUG", "false").lower() == "true":
    logging.basicConfig(
        filename="my_log.log", level=logging.INFO, filemode="w",
        format="%(asctime)s %(levelname)s %(message)s",
    )
    def log(message, *args, **kwargs):
        logging.info(message, *args, **kwargs)
else:
    def log(message, *args, **kwargs):
        pass


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


def get_adjacent_positions(position):
    """
    Return the adjacent positions of a position.
    """
    x, y = position
    return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]


def distance(position1, position2):
    """
    Return the distance between two positions.
    """
    x1, y1 = position1
    x2, y2 = position2

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

DEFENSIVE_MODE = "defensive"
AGGRESSIVE_MODE = "aggressive"
MODES = (
    DEFENSIVE_MODE,
    AGGRESSIVE_MODE,
)

COST_STRUCT_TO_CONQUER = (
    ("land", 1),
    ("farm", 2),
    ("near_castle", 25),
    ("fort", 50),
    ("castle", 100),
)

def world_saver(func):
    """
    I use this decorator to do some things after to return the action.
    - Save the world in the previous_world attribute.
    - Update the tick_since_harvest attribute.
    - Make the correct action, avoiding to lose the turn.
    """
    def wrapper(self, *args, **kwargs):
        action, pos = func(self, *args, **kwargs)
        log(f"action: {action}, pos: {pos}, self {self}")
        self.my_resources = args[1]
        self.previous_world = args[2]
        if action == "harvest":
            self.tick_since_harvest = 0
        else:
            self.tick_since_harvest += 1

        # this is an attemp to make the correct action, avoiding to lose the turn
        result = self.safe_action(action, pos, self.previous_world, self.my_resources)
        log(f"action: {result}")
        self.previous_action = result
        return result
    return wrapper


class BotLogic:
    my_castles = []
    mode = DEFENSIVE_MODE
    can_build_castle = False

    previous_world = {}
    previous_action = "harvest", None
    lost_land = []
    tick_since_harvest = 0

    @world_saver
    def turn(self, map_size, my_resources, world):
        """
        I want to build a bot that combines a 65% of aggressive and 35% of defensive.
        """
        self.my_castles = [
            position for position, terrain in world.items()
            if terrain.owner == "mine" and terrain.structure == "castle"
        ]
        self.enemy_castles = [
            position for position, terrain in world.items()
            if terrain.owner != "mine" and terrain.structure == "castle"
        ]
        self.my_terrains = [
            position for position, terrain in world.items()
            if terrain.owner == "mine"
        ]
        self.terrain_available_to_act = [
            position for position, terrain in world.items()
            if terrain.owner != "mine" and self.is_adjacent_to_my_empires(position, world)
        ]
        self.can_build_castle = self._can_build_castle(my_resources, world)
        stats = self._calc_stats_from_world(world)
        self.enemies_amount = len(stats["participants"]) - 1

        self.lost_land = self._conquered_land(world)
        log("I lost in the last turn: %s", self.lost_land)
        
        if my_resources < 25:
            return "harvest", None
        
        for inmediate_action, elem in self._has_inmediate_action(world):
            pos, _ = elem
            if self._determine_cost_to_conquer(pos, world) <= my_resources:
                log("inmediate_action: %s, pos: %s", inmediate_action, pos)
                return inmediate_action, pos
            
        if self.tick_since_harvest > 10:
            return "harvest", None

        percent_to_change_mode = 0.1 - (self.enemies_amount * 0.01)
        if stats["percentage_of_lands"]["mine"] > percent_to_change_mode:
            self.mode = AGGRESSIVE_MODE
        else:
            self.mode = DEFENSIVE_MODE
        
        log("mode: %s", self.mode)

        if self.mode == "defensive":
            # first part of the game: get resource and defend
            # make farms and forts as concentric circles around the castle
            my_lands = [position for position, terrain in world.items()
                        if terrain.owner == "mine" and terrain.structure == "land"]
            if my_lands:
                if self.previous_action[0] == "conquer" and len(self.lost_land) > 0:
                    lost = Counter(self.lost_land).most_common()
                    for land, count in lost:
                        if land in self.terrain_available_to_act:
                            if self.can_build_castle:
                                return "castle", land
                            else:
                                if self._determine_cost_to_conquer(land, world) <= my_resources:
                                    return "fort", land
                                else:
                                    return "farm", land
                    
                dist_castle = min([
                    int(round(distance(my_lands[0], castle)))
                    for castle in self.my_castles
                ])
                
                log("dist_castle: %s", dist_castle)
                if dist_castle > 1 and dist_castle <5 and my_resources > 50:
                    return "fort", my_lands[0]
                elif self.can_build_castle:
                    return "castle", my_lands[0]
                else:
                    return "farm", my_lands[0]
            else:
                neutral_lands = self._get_neutral_land_around_castle(self.my_castles[-1], world)
                for land in neutral_lands:
                    if self._determine_cost_to_conquer(land, world) <= my_resources:
                        return "conquer", land
        elif self.mode == "aggressive":
            # second part of the game: attack
            # find the closest enemy castle to my lands
            next_conquer_position = []
            if all([self.terrain_available_to_act, self.enemy_castles]):
                for adj_pos in self.terrain_available_to_act:
                    for castle_pos in self.enemy_castles:
                        next_conquer_position.append((adj_pos, distance(adj_pos, castle_pos)))
                next_conquer_position = sorted(next_conquer_position, key=lambda x: x[1])
                for attemp in next_conquer_position:
                    if attemp[0] in self.terrain_available_to_act and self._determine_cost_to_conquer(attemp[0], world) <= my_resources:
                        return "conquer", attemp[0]

        return "harvest", None

    def is_adjacent_to_my_empires(self, land, world):
        # filter lands list if each one is adjacent to my lands
        for my_tile in self.my_terrains:
            if is_adjacent(land, my_tile):
                return True
        return False

    def _get_neutral_land_around_castle(self, castle_position, world):
        """
        Get all the neutral land around the castle.
        """
        lands = [
            (position, distance(position, castle_position)) 
            for position, terrain in world.items()
            if terrain.owner == None and position in self.terrain_available_to_act
        ]
        return list(map(lambda x: x[0], sorted(lands, key=lambda x: x[1])))
    
    def _get_enemy_land_around_castle(self, castle_position, world) -> list[tuple[Position, Terrain, int]]:
        """
        Get all the enemy land around the castle.
        """
        temp = [
            (position, terrain, math.ceil(distance(position, castle_position))) 
            for position, terrain in world.items()
            if terrain.owner != "mine"
        ]
        # filters by distance
        temp = list(filter(lambda x: x[2] <= 2, temp))
        # sort by distance
        temp = sorted(temp, key=lambda x: x[2])
        return temp
    
    def _can_build_castle(self, my_resources, world):
        """
        Check if we can build a castle.
        """
        return len(self.my_terrains)/50 > len(self.my_castles) and my_resources > 75

    def _has_inmediate_action(self, world):
        """
        Check if we have an inmediate action to do.
        """
        for castle in self.my_castles:
            if near_to_castle := self._get_enemy_land_around_castle(castle, world):
                for elem in near_to_castle:
                    if elem[0] in self.terrain_available_to_act:
                        yield "conquer", (elem[0], elem[1])
    
    def _conquered_land(self, world) -> list[Position]:
        """
        Get all the conquered land that in previous_world were mine.
        """
        if self.previous_world: 
            return [
                position for position, terrain in world.items() if terrain.owner != "mine" and self.previous_world[position].owner == "mine"
            ]
        return []
    
    def _calc_stats_from_world(self, world):
        """
        Calculate the stats from the world.
        - Amount of participants
        - Percentage ff lands by participants
        """
        tiles_amount = len(world.keys())
        land_owner = Counter(list(terrain.owner for terrain in world.values()))
        percentage_of_lands = {}
        for participant, count in land_owner.items():
            percentage_of_lands[participant] = count / tiles_amount
        return {
            "participants": set(land_owner),
            "percentage_of_lands": percentage_of_lands
        }

    def _determine_cost_to_conquer(self, target_position, world):
        """
        Determine the cost to conquer a tile.
        """
        if target_position in self.my_terrains:
            return 0
        costs = dict(COST_STRUCT_TO_CONQUER)
        cost_list = [costs[world[target_position].structure]]
        for adj_pos in get_adjacent_positions(target_position):
            if adj_pos in world:
                if world[adj_pos].owner not in ("mine", None) and world[adj_pos].structure in ("castle", "fort"):
                    cost_list.append(costs["near_castle"])
        return max(cost_list)

    def safe_action(self, action, position, world, my_resources):
        """
        Try to minimaze the risk of losing the turn.
        """
        if action == "conquer":
            if self._determine_cost_to_conquer(position, world) <= my_resources:
                return action, position
            else:
                return "harvest", None
        return action, position
        
