from game import Position, Terrain
import random
import math
import logging

def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


STRUCTURE_COST = {
    "farm": 5,
    "fort": 25,
    "castle": 75,
}

class BotLogic:
    def turn(self, map_size, my_resources, world):

        def nearest_point(points, target, world, objective=None):
            """
            Encuentra el punto más cercano a 'target' dentro de 'points'.

            target: (x, y) - Coordenada objetivo.
            points: [(x1, y1), (x2, y2), ...] - Lista de coordenadas.

            Retorna la coordenada más cercana y su distancia.
            """
            min_distance = float('inf')
            closest = None

            for point in points:
                # Distancia Euclidiana: sqrt((x2 - x1)^2 + (y2 - y1)^2)
                if objective != None:
                    world_objectives = [x for x in world if world[x].structure == objective and world[x].owner != "mine"]
                    return nearest_point((conquerable_neutral_terrain + enemy_terrain_near), world_objectives[0], world)


                distance = math.sqrt((point.x - target.x)**2 + (point.y - target.y)**2)

                if distance < min_distance:
                    min_distance = distance
                    closest = point

            return closest

        my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
        my_castles = [x for x in my_terrain if world[x].structure == "castle"]


        enemy_terrain_near = [
            position
            for position, terrain in world.items()
            if terrain.owner not in ("mine", None) and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]

        conquerable_neutral_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner is None and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]

        if my_resources <= 10:
            return "harvest", None

        if len(enemy_terrain_near) > 0:
            for my_position in my_terrain:
                for position, terrain in world.items():
                    if terrain.owner not in ("mine", None) and is_adjacent(position, my_position):
                        if world[my_position].structure not in ("castle", "fort"):
                            if my_resources >= 75:
                                return "castle", my_position
            else:
                if my_resources >= 100:
                    return "conquer", nearest_point(enemy_terrain_near, my_castles[-1], world, objective="castle")
                else:
                    return "harvest", None
        else:
            to_build = [x for x in my_terrain if world[x].structure == "land"]

            if len(to_build) > 0:
                return "farm", nearest_point(to_build, my_castles[0], world)
            elif len(conquerable_neutral_terrain) > 0:
                return "conquer", nearest_point(conquerable_neutral_terrain, my_castles[-1], world)

        if len(conquerable_neutral_terrain) > 0:
            return "conquer", conquerable_neutral_terrain[random.randint(0, len(conquerable_neutral_terrain))]

        return "harvest", None
