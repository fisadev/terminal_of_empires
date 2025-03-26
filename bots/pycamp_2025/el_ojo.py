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


def nearest_position_to(list_of_positions, center_position):

    nearest_position = list_of_positions[0]

    for position in list_of_positions:
            if distance(center_position, position) < distance(center_position, nearest_position):
                nearest_position = position

    return nearest_position


class BotLogic:
    """
    Bot logic for the Zanahoria bot.
    """

    # Steps:
    # 1. Build farms
    # 2. Build walls
    # 3. Build a castle
    # 4. if there's an enemy close 
        # conquer

    first_turn = True
    castle_position = (0,0)

    def turn(self, map_size, my_resources, world):

        if my_resources < 10:
            return "harvest", None


        my_land    = [position for position, terrain in world.items()
                            if terrain.owner == "mine"]

        my_castles = [position for position, terrain in world.items()
                         if terrain.owner == "mine" and terrain.structure == "castle"]

        my_empty_land = [position for position, terrain in world.items()
                            if terrain.owner == "mine" and terrain.structure == "land"]

        if self.first_turn:
            all_the_castles = [position for position, terrain in world.items()
                            if terrain.owner == "mine" and terrain.structure == "castle"]
            self.castle_position = all_the_castles[0]
            self.first_turn = False

        if my_empty_land:

            if len(my_land) / len(my_castles) > 50:
                plan       = ["castle", "fort"]
                plan_costs = [75, 25]
            else:
                plan       = ["farm", "fort"]
                plan_costs = [5, 25]

            nearest_empty_position = nearest_position_to(my_empty_land, self.castle_position)
            distance_to_center     = distance(nearest_empty_position, self.castle_position)
            
            plan_index = round(distance_to_center)%2

            if my_resources < plan_costs[plan_index]:
                return "harvest", None
            else:
                return plan[plan_index], nearest_empty_position
            
        conquerable_terrain_in_reach = [
            position
            for position, terrain in world.items()
            if terrain.owner != "mine" and any(
                is_adjacent(position, my_position)
                for my_position in my_land
            )
        ]

        if conquerable_terrain_in_reach:

            nearest_conquerable_position = nearest_position_to(conquerable_terrain_in_reach, self.castle_position)
            nearest_conquerable_position_structure = world[nearest_conquerable_position].structure

            if nearest_conquerable_position_structure == "land"   and my_resources > 1: 
                return "conquer", nearest_conquerable_position
            if nearest_conquerable_position_structure == "farm"   and my_resources > 5: 
                return "conquer", nearest_conquerable_position
            if nearest_conquerable_position_structure == "fort"   and my_resources > 25: 
                return "conquer", nearest_conquerable_position
            if nearest_conquerable_position_structure == "castle" and my_resources > 100: 
                return "conquer", nearest_conquerable_position

        # finally, if nothing could be done, harvest
        return "harvest", None
