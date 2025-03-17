import random


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


class BotLogic:
    """
    Bot logic for the Pacifist bot.
    """
    def turn(self, map_size, my_resources, world):
        """
        Pacifist bot either tries to build farms, or conquer neutral terrain.
        It tries to keep its resources just high enough to do that.
        """
        # try to keep resources high enough to build a farm or conquer empty neutral land
        if my_resources < 5:
            return "harvest", None

        if random.random() < 0.2:
            # try to build a farm
            my_empty_land = [position for position, terrain in world.items() if terrain.owner == "mine" and terrain.structure == "land"]

            if my_empty_land:
                return "farm", random.choice(my_empty_land)
        else:
            # try to conquer empty land
            my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
            conquerable_neutral_terrain = [
                position
                for position, terrain in world.items()
                if terrain.owner is None and any(
                    is_adjacent(position, my_position)
                    for my_position in my_terrain
                )
            ]

            if conquerable_neutral_terrain:
                return "conquer", random.choice(conquerable_neutral_terrain)

        # finally, if nothing could be done, harvest
        return "harvest", None
