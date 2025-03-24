import random

from game import DEFENDER_STRUCTURES, Position


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


def distance(position1, position2):
    """
    Return the distance between two positions.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2)


def adjacent_positions_data(position, world):
    """
    Return the valid positions adjacent to the given position, considering the map size.
    """
    x, y = position
    for adjacent_position in [
        Position(x - 1, y),
        Position(x + 1, y),
        Position(x, y - 1),
        Position(x, y + 1),
    ]:
        position_data = world.get(adjacent_position)
        if position_data is not None:
            yield adjacent_position, position_data


def conquer_cost(target_data, world):
    target_position, target = target_data
    conquer_costs = {
        None: (0, ),
        "castle": (100, ),
        "fort": (50, ),
        "land": (1, 25),
        "farm": (2, 25),
    }
    costs = conquer_costs[target.structure]
    if len(costs) == 1:
        return costs[0]
    else:   
        is_defended = any(
            adjacent.structure in DEFENDER_STRUCTURES
            and adjacent.owner == target.owner
            for _, adjacent in adjacent_positions_data(target_position, world)
        )
        if is_defended:
            return costs[1]
        else:
            return costs[0]

class BotLogic:
    """
    Bot logic for the simple_mix bot.
    """

    def __init__(self):
        self.force_aggressive = False
        self.agressiveness_level = 0.7  # como el ferné

    def _others_distance(
        self, comparison_function, position, world_tuples, only_structures=None, default_val=0.0
    ):
        return comparison_function(
            (
                distance(position, other_position)
                for other_position, other_terrain in world_tuples
                if other_terrain.owner != "mine"
                and (only_structures is None or other_terrain.structure in only_structures)
            ),
            default=default_val
        )

    def others_max_distance(self, position, world_tuples, only_structures=None):
        return self._others_distance(
            max, position, world_tuples, only_structures=only_structures, default_val=0.0
        )

    def others_min_distance(self, position, world_tuples, only_structures=None):
        return self._others_distance(
            min, position, world_tuples, only_structures=only_structures, default_val=1e100
        )

    def aggressive_turn(self, map_size, my_resources, world):
        """
        Aggressive always tries to conquer terrain, and never builds any structures.
        It prioritizes conquering enemy terrain over neutral land.
        It tries to keep its resources high, so it can deal with any kind of enemy defenses.
        """
        my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
        conquerable_terrain = [
            (position, terrain)
            for position, terrain in world.items()
            if terrain.owner != "mine" and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]

        if conquerable_terrain:
            conquerable_castle_positions = [
                position for position, terrain in conquerable_terrain 
                if terrain.structure == "castle"
            ]
            if conquerable_castle_positions:
                if my_resources < 100:
                    # wait for the next turn to conquer the castle
                    self.force_aggressive = "aggressive"
                    return "harvest", None
                else:
                    return "conquer", random.choice(conquerable_castle_positions)
            best_conquer = min(
                conquerable_terrain,
                key=lambda position_data: self.others_min_distance(
                    position_data[0], world.items(), only_structures={"castle"},
                )
            )
            if my_resources >= conquer_cost(best_conquer, world):
                return "conquer", best_conquer[0]

        # finally, if nothing could be done, harvest
        return "harvest", None

    def defensive_turn(self, map_size, my_resources, world):
        if my_resources < 25:
            # try to always have enough resources for a fort, in case we need to build one
            return "harvest", None

        my_empty_land = [(position, terrain) for position, terrain in world.items()
                         if terrain.owner == "mine" and terrain.structure == "land"]
        if my_empty_land:

            if my_resources >= 75:
                my_terrain = [(position, terrain) for position, terrain in world.items()
                              if terrain.owner == "mine"]
                castles = len([(position, terrain) for position, terrain in my_terrain
                               if terrain.structure == "castle"])
                if castles * 50 < len(my_terrain):
                    # The best land to put a fort is the farest away from the others, so it takes
                    # more turns to be conquered
                    best_land = max(
                            my_empty_land,
                            key=lambda position_data: self.others_max_distance(
                                position_data[0], world.items(),
                            )
                        )
                    return "castle", best_land[0]
            # the closest to a castle to protect it
            my_castle_positions = [
                (position, terrain) for position, terrain in world.items()
                if terrain.owner == "mine" and terrain.structure == "castle"
            ]
            best_land = min(
                my_empty_land,
                key=lambda position_data: self.others_min_distance(
                    position_data[0], my_castle_positions, 
                )
            )
            return "fort", best_land[0]

        # no more empty land, so try to conquer any terrain with the agressive strategy
        return self.aggressive_turn(map_size, my_resources, world)

    def turn(self, map_size, my_resources, world):
        """
        A bot that combines all basic strategies with a given probability for each
        (with some tweaks in the basic strategies).
        """

        if self.force_aggressive:
            self.force_aggressive = False
            return self.aggressive_turn(map_size, my_resources, world)

        turn_random_val = random.random()
        if turn_random_val < self.agressiveness_level:
            return self.aggressive_turn(map_size, my_resources, world)
        else:
            return self.defensive_turn(map_size, my_resources, world)
