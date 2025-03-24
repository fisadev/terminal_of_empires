import random
import math


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

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def closest_position_to_any_castle(world, positions):

    castles = [position for position, terrain in world.items()
                            if terrain.owner != "mine" and terrain.structure == "castle"]
    
    closest_castle   = castles[0]
    closest_position = positions[0]

    for position in positions:
        for castle in castles:
            if distance(position, castle) < distance(closest_position, closest_castle):
                        closest_castle   = castle
                        closest_position = position

    return closest_position, closest_castle

class BotLogic:

    conquer_costs = {"castle":100, "fort":50,"farm":25,"land":1}
    
    
    def turn(self, map_size, my_resources, world):
        
        if my_resources < 5:
            return "harvest", None

        my_empty_land = [position for position, terrain in world.items()
                         if terrain.owner == "mine" and terrain.structure == "land"]

        if my_empty_land:
            return "farm", my_empty_land[0]


        # no more empty land, so try to conquer any terrain
        my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
        conquerable_terrain_in_reach = [
            position
            for position, terrain in world.items()
            if terrain.owner != "mine" and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]


        if conquerable_terrain_in_reach:

            next_position, _ = closest_position_to_any_castle(world, conquerable_terrain_in_reach)
            if self.conquer_costs[world[next_position].structure] <= my_resources:
                return "conquer", next_position

        #if conquerable_terrain_in_reach and my_resources > 100:
#
        #    next_position, _ = closest_position_to_any_castle(world, conquerable_terrain_in_reach)
        #    return "conquer", next_position

        # finally, if nothing could be done, harvest
        return "harvest", None