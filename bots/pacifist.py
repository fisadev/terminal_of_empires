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
        Pacifist bot always tries to conquer neutral terrain, and never builds anything.
        It tries to keep its resources just high enough to conquery empty land.
        """
        # keep the resources high so we can conquer anything we want
        if my_resources == 0:
            return "harvest", None

        # if we have resources, try to conquer empty land
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
