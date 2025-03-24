from game import Position, Terrain
import random
import math
import logging

def get_adjacent_coord(position):
    x1, y1 = position
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [(x1 + dx, y1 + dy) for dx, dy in deltas]

def is_adjacent(position1, position2, distance=1, vertically=False):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1.x, position1.y
    x2, y2 = position2.x, position2.y

    if vertically:
        if (abs(x1 - x2) == distance and y1 == y2) or (abs(y1 - y2) == distance and x1 == x2):
            return True
        if abs(x1-x2) == distance and abs(y1 - y2) == distance:
            return True
        
        return False


    return abs(x1 - x2) + abs(y1 - y2) <= distance

def nearest_point(points, targets, world, castle_enemy=False, castles_info={}, furthest=False):
    """
    Encuentra el punto más cercano a 'target' dentro de 'points'.

    target: (x, y) - Coordenada objetivo.
    points: [(x1, y1), (x2, y2), ...] - Lista de coordenadas.

    Retorna la coordenada más cercana y su distancia.
    """

    min_distance_castle = float('inf')
    min_distance = float('inf')
    closest = None
    closest_enemy_castle = None
    max_distance = 0

    if castle_enemy:
        for owner, positions in castles_info.items():
            if owner != "mine":
                for position in positions:
                    for point in points:
                        distance = math.sqrt((point.x - position.x)**2 + (point.y - position.y)**2)

                        if distance < min_distance_castle:
                            min_distance_castle = distance
                            closest_enemy_castle = point


    for point in points:
        # Distancia Euclidiana: sqrt((x2 - x1)^2 + (y2 - y1)^2)    
        for target in targets:
            distance = math.sqrt((point.x - target.x)**2 + (point.y - target.y)**2)

            if furthest:
                if max_distance < distance:
                    max_distance = distance
                    far = point
            
            else:
                if distance < min_distance:
                    min_distance = distance
                    closest = point

    if castle_enemy and min_distance <= 4:
        return closest
    elif castle_enemy:
        return closest_enemy_castle

    if furthest:
        return far
    else:
        return closest

def is_alive(castles_people, enemy_terrain_near, world):
    for position in enemy_terrain_near:
        if castles_people.get(world[position].owner) != None:
            return True
    else:
        return False
class BotLogic:
    turns = 0

    def __init__(self):
        self.turns = 0

    def turn(self, map_size, my_resources, world):
        self.turns += 1
        my_terrain = set()
        my_castles = set()
        enemy_terrain_near = set()
        conquerable_neutral_terrain = set()
        castles_people = {}
        to_build = set()
        castles_target = set()

        #preparing lists and data
        for position, terrain in world.items():
            if terrain.owner == "mine":
                my_terrain.add(position)
                if terrain.structure == "castle":
                    my_castles.add(position)

                elif terrain.structure == "land":
                    to_build.add(position)

                for adjacent in get_adjacent_coord(position):
                    try:
                        adjacent_obj = Position(adjacent[0], adjacent[1])
                        owner = world[adjacent_obj].owner

                        if world.get(adjacent_obj) != None:
                            if owner not in ("mine", None):
                                enemy_terrain_near.add(adjacent_obj)

                            elif owner == None:
                                conquerable_neutral_terrain.add(adjacent_obj)

                    except:
                        pass

            if terrain.structure == "castle":
                if castles_people.get(terrain.owner) == None:
                    castles_people[terrain.owner] = [position]
                else:
                    castles_people[terrain.owner].append(position)

                if terrain.owner not in (None, "mine"):
                    castles_target.add(position)
    
        #end of preparing data

        if self.turns > 250 and len(my_castles) > 2:
            mode = "attack"
        else:
            mode = "expand"

        if my_resources <= 10:
            return "harvest", None
        elif my_resources >= 100 and (len(my_terrain) / len(my_castles)) > 50:
            if world[position].structure not in ("castle", "fort"):
                return "castle", nearest_point(frozenset(my_terrain), frozenset(my_castles), world, furthest=True)


        if len(enemy_terrain_near) > 0 or mode == "attack":
            if mode == "attack" and len(enemy_terrain_near) == 0:
                position = nearest_point(conquerable_neutral_terrain, my_castles, world, castle_enemy=True, castles_info=castles_people)
            else:
                position = nearest_point(enemy_terrain_near, my_castles, world, castle_enemy=True, castles_info=castles_people)
            
            if my_resources > 100:
                return "conquer", position
            else:
                return "harvest", None

        if not is_alive(castles_people, enemy_terrain_near, world) and mode == "expand":
            to_build = [x for x in my_terrain if world[x].structure == "land"]

            if len(to_build) > 0:
                return "farm", nearest_point(frozenset(to_build), frozenset(my_castles), world)
            
            elif len(conquerable_neutral_terrain) > 0:
                position = nearest_point(frozenset(conquerable_neutral_terrain), frozenset(my_castles), world)
                return "conquer", position

        return "harvest", None