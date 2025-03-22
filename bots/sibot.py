from game import Position, Terrain
import random
import math
import logging

def is_adjacent(position1, position2, distance=1):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= distance


STRUCTURE_COST = {
    "farm": 5,
    "fort": 25,
    "castle": 75,
}

class BotLogic:
    last_turn = None
    def turn(self, map_size, my_resources, world):

        def nearest_point(points, target, world, castle_enemy=False, castles_info={}):
            """
            Encuentra el punto más cercano a 'target' dentro de 'points'.

            target: (x, y) - Coordenada objetivo.
            points: [(x1, y1), (x2, y2), ...] - Lista de coordenadas.

            Retorna la coordenada más cercana y su distancia.
            """
            min_distance = float('inf')
            closest = None

            if castle_enemy:
                for owner, positions in castles_info.items():
                    if owner != "mine":
                        for position in positions:
                            for point in points:
                                distance = math.sqrt((point.x - position.x)**2 + (point.y - position.y)**2)

                                if distance < min_distance:
                                    min_distance = distance
                                    closest = point
                return closest


            for point in points:
                # Distancia Euclidiana: sqrt((x2 - x1)^2 + (y2 - y1)^2)    

                distance = math.sqrt((point.x - target.x)**2 + (point.y - target.y)**2)

                if distance < min_distance:
                    min_distance = distance
                    closest = point

            return closest

        def is_alive(castles_people, enemy_terrain_near, world):
            for position in enemy_terrain_near:
                if castles_people.get(world[position].owner) != None:
                    return True
            else:
                return False
                    

        my_terrain = [] 
        my_castles = [] 
        enemy_terrain_near = []
        conquerable_neutral_terrain = []
        castles_people = {}
        pre_protection = []

        #preparing lists and data
        for position, terrain in world.items():
            if terrain.owner == "mine":
                my_terrain.append(position)
                if terrain.structure == "castle":
                    my_castles.append(position)

            if terrain.structure == "castle":
                if castles_people.get(terrain.owner) == None:
                    castles_people[terrain.owner] = [position]
                else:
                    castles_people[terrain.owner].append(position)
        
        for my_position in my_terrain:
            for position, terrain in world.items():
                if terrain.owner not in ("mine", None) and is_adjacent(position, my_position) and castles_people.get(terrain.owner) != None:
                    enemy_terrain_near.append(position)

                elif is_adjacent(position, my_position) and terrain.owner != "mine":
                    conquerable_neutral_terrain.append(position)

                if is_adjacent(position, my_position, 2) and terrain.owner not in ("mine", None) and world[my_position].structure not in ("fort", "castle"):
                    pre_protection.append((position, my_position))
    
        #end of preparing data

        if my_resources <= 10:
            return "harvest", None
        if my_resources >= 100 and (len(my_terrain) / len(my_castles)+1) >= 50:
            while True:
                position = random.choice(my_terrain)
                if world[position].structure not in ("castle", "fort"):
                    return "castle", random.choice(my_terrain)
                
        if len(enemy_terrain_near) > 0:
            if my_resources > 100:
                return "conquer", nearest_point(enemy_terrain_near, my_castles[0], world, castle_enemy=True, castles_info=castles_people)
            else:
                return "harvest", None

        elif len(pre_protection) > 0 and my_resources >= 25:
            for positions in pre_protection:
                if castles_people.get(world[positions[0]].owner) != None:
                    return "fort", positions[1]

        if not is_alive(castles_people, enemy_terrain_near, world):
            to_build = [x for x in my_terrain if world[x].structure == "land"]

            if len(to_build) > 0:
                return "farm", nearest_point(to_build, my_castles[0], world)
            elif len(conquerable_neutral_terrain) > 0:
                return "conquer", nearest_point(conquerable_neutral_terrain, my_castles[-1], world)

        return "harvest", None
