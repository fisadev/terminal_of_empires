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
    Bot logic for the Aggressive bot.
    """
    def turn(self, map_size, my_resources, world):
        """
        Aggressive bot always tries to conquer terrain, and never builds any structures.
        It prioritizes conquering enemy terrain over neutral land.
        It tries to keep its resources high, so it can deal with any kind of enemy defenses.
        """
        # try to find enemy terrain that we can conquer
        my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
        conquerable_enemy_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner not in ("mine", None) and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]

        if conquerable_enemy_terrain:
            # keep the resources high so we can conquer anything we want
            if my_resources < 100:
                return "harvest", None
            else:
                return "conquer", random.choice(conquerable_enemy_terrain)

        # if no enemy terrain, then try to conquer neutral terrain
        conquerable_neutral_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner is None and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]

        if conquerable_neutral_terrain:
            if my_resources < 1:
                return "harvest", None
            else:
                return "conquer", random.choice(conquerable_neutral_terrain)

        # finally, if nothing could be done, harvest
        return "harvest", None
