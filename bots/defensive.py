import random


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


class BotLogic:
    """
    Bot logic for the Defensive bot.
    """
    def turn(self, map_size, my_resources, world):
        """
        Defensive bot that tries to build forts in every bit of land it conquers. But as it doesn't
        build farms, it has very little production.
        """
        if my_resources < 25:
            # try to always have enough resources for a fort, in case we need to build one
            return "harvest", None

        my_empty_land = [position for position, terrain in world.items()
                         if terrain.owner == "mine" and terrain.structure == "land"]
        if my_empty_land:
            # we can build a fort!
            return "fort", random.choice(my_empty_land)

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
            return "conquer", random.choice(conquerable_terrain_in_reach)

        # finally, if nothing could be done, harvest
        return "harvest", None
